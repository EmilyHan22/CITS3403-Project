from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash,jsonify, current_app
)
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from app import mail, make_serializer
from flask_login import (
    login_user, logout_user,
    current_user, login_required
)
from app.db import db
from app.models import User, Podcast, Friendship,PodcastLog
from datetime import datetime, date
import sys
import os
import requests
from urllib.parse import urlencode

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

bp = Blueprint("main", __name__)

@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user  = User.query.filter_by(email=email).first()
        if not user:
            flash("That email address isn’t registered.", "danger")
            return redirect(url_for("main.forgot_password"))

        token = make_serializer(current_app).dumps(user.email)
        link  = url_for("main.reset_password", token=token, _external=True)

        msg = Message(
            subject="Podfolio Password Reset",
            recipients=[user.email],
            body=(
                f"Hi {user.username},\n\n"
                f"Click here to reset your password:\n{link}\n\n"
                "If you didn’t request this, just ignore this email."
            )
        )
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error("Failed to send reset email", exc_info=e)
            flash("Error sending reset email. Please try again later.", "danger")
            return redirect(url_for("main.forgot_password"))

        flash("Check your inbox for a reset link.", "success")
        # stay on this page so the success message is shown here
        return redirect(url_for("main.forgot_password"))

    return render_template("forgot_password.html", current_year=date.today().year)

@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    try:
        email = make_serializer(current_app).loads(token, max_age=3600)
    except SignatureExpired:
        flash("This reset link has expired.", "warning")
        return redirect(url_for("main.forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "danger")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        new_pw = request.form.get("password", "")
        cpw = request.form.get("confirm_password", "")
        if new_pw != cpw:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.reset_password", token=token))
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_pw)
            db.session.commit()
            flash("Your password has been reset. You can now log in.", "success")
            return redirect(url_for("main.login"))
        flash("User account not found.", "danger")
        return redirect(url_for("main.signup"))

    return render_template(
        "reset_password.html",
        token=token,
        current_year=date.today().year
    )

# ─── Public routes ────────────────────────────────────────────

@bp.route("/")
def index():
    # If already logged in, send straight to podcast-log
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))
    return render_template(
        "index.html",
        current_year=date.today().year
    )

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    # Redirect logged-in users away
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        data = request.form
        if data["password"] != data["confirm_password"]:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.signup"))
        # 1) Prevent duplicate usernames
        if User.query.filter_by(username=data["username"]).first():
            flash("Username already taken.", "warning")
            return redirect(url_for("main.signup"))

        # 2) Prevent duplicate emails
        if User.query.filter_by(email=data["email"]).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("main.signup"))

        # 3) Create & commit the new user
        user = User(
            username     = data["username"],
            email        = data["email"],
            display_name = f"{data['first_name']} {data['last_name']}"
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()

        # 4) Log them in and redirect to dashboard
        login_user(user)
        return redirect(url_for("main.podcast_log"))

    # GET → show sign-up form
    return render_template(
        "signup.html",
        current_year=date.today().year
    )

@bp.route("/login", methods=["GET", "POST"])
def login():
    # Redirect logged-in users away
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        email    = request.form.get("email", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            # honor ?next=… if provided
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.podcast_log"))

        flash("Invalid credentials.", "danger")
        return redirect(url_for("main.login"))

    # GET → show login form
    return render_template(
        "login.html",
        current_year=date.today().year
    )

# ─── Protected routes ─────────────────────────────────────────

@bp.route("/podcast-log", methods=["GET", "POST"])
@login_required
def podcast_log():
    if request.method == "POST":
        # TODO: handle form submission for logging a podcast
        return redirect(url_for("main.podcast_log"))

    return render_template(
        "PodcastLog.html",
        current_year=date.today().year
    )

@bp.route("/shareview")
@login_required
def share():
    return render_template(
        "shareview.html",
        current_year=date.today().year
    )

@bp.route("/visualise")
@login_required
def visualise():
    return render_template(
        "visualise.html",
        current_year=date.today().year
    )

@bp.route("/frienddash")
@login_required
def frienddash():
    return render_template(
        "frienddash.html",
        current_year=date.today().year
    )

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@bp.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    username = request.json.get('username')
    friend = User.query.filter_by(username=username).first()
    
    if not friend:
        return jsonify({'error': 'User not found'}), 404
        
    if current_user.id == friend.id:
        return jsonify({'error': 'Cannot add yourself'}), 400
        
    # Check if friendship already exists
    existing = Friendship.query.filter_by(
        user_id=current_user.id,
        friend_id=friend.id
    ).first()
    
    if existing:
        return jsonify({'error': 'Already friends'}), 400
        
    # Create relationship
    friendship = Friendship(user_id=current_user.id, friend_id=friend.id)
    db.session.add(friendship)
    db.session.commit()
    
    return jsonify({
        'message': f'Added {username} as friend',
        'friend': {
            'id': friend.id,
            'username': friend.username
        }
    })
@bp.route('/remove_friend/<int:friend_id>', methods=['DELETE'])
@login_required
def remove_friend(friend_id):
    # Remove only your following (one-way)
    friendship = Friendship.query.filter_by(
        user_id=current_user.id,
        friend_id=friend_id
    ).first()
    
    if not friendship:
        return jsonify({'error': 'Not currently following this user'}), 404
        
    db.session.delete(friendship)
    db.session.commit()
    
    return jsonify({'message': 'Removed from your following'})

@bp.route('/search_podcast_names')
@login_required
def search_podcast_names():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    podcasts = Podcast.query.filter(
        Podcast.name.ilike(f'%{query}%')
    ).with_entities(Podcast.id, Podcast.name).limit(10).all()
    
    return jsonify([{'id': p.id, 'name': p.name} for p in podcasts])

@bp.route('/log_podcast', methods=['POST'])
@login_required
def log_podcast():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid content type'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('podcast_id'):
        return jsonify({'success': False, 'message': 'Podcast is required'}), 400
    
    try:
        podcast = Podcast.query.filter_by(spotify_id=data['podcast_id']).first()
        
        if not podcast:
            # Fetch podcast details from Spotify to save in our DB
            token = get_spotify_token()
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                f'https://api.spotify.com/v1/shows/{data["podcast_id"]}',
                headers=headers
            )
            show_data = response.json()
            
            podcast = Podcast(
                spotify_id=show_data['id'],
                name=show_data['name'],
                description=show_data['description'],
                # Map other fields as needed
            )
            db.session.add(podcast)
            db.session.commit()
        podcast_log = PodcastLog(
            user_id=current_user.id,
            podcast_id=podcast.id,
            notes=data.get('episode'),
            tags=data.get('platform'),
            duration=int(data.get('duration', 0)) * 60 if data.get('duration') else None,
            rating=float(data['rating']) if data.get('rating') else None
        )
        
        db.session.add(podcast_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Podcast logged successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error logging podcast: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)  # Be cautious about exposing errors in production
        }), 500
def get_spotify_token():
    """Get Spotify API access token"""
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(
        auth_url,
        data={'grant_type': 'client_credentials'},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return auth_response.json().get('access_token')

@bp.route('/search_spotify_podcasts')
@login_required
def search_spotify_podcasts():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        token = get_spotify_token()
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': query,
            'type': 'show',
            'market': 'US',  # Adjust based on your target market
            'limit': 10
        }
        
        response = requests.get(
            'https://api.spotify.com/v1/search',
            headers=headers,
            params=params
        )
        
        shows = response.json().get('shows', {}).get('items', [])
        
        results = [{
            'id': show['id'],
            'name': show['name'],
            'publisher': show['publisher'],
            'image': show['images'][0]['url'] if show['images'] else None
        } for show in shows]
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Spotify search error: {str(e)}")
        return jsonify([])

@bp.route('/callback')
def spotify_callback():
    # Handle authorization code if using OAuth
    code = request.args.get('code')
    # Exchange code for token here
    return redirect(url_for('main.podcast_log'))