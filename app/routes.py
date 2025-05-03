from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, jsonify
)
from flask_login import (
    login_user, logout_user,
    current_user, login_required
)
from app.db import db
from app.models import User, Podcast, Friendship
import datetime
import sys

bp = Blueprint("main", __name__)

# ─── Public routes ────────────────────────────────────────────

@bp.route("/")
def index():
    # If already logged in, send straight to podcast-log
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))
    return render_template(
        "index.html",
        current_year=datetime.date.today().year
    )

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    # Redirect logged-in users away
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        # debug print to stderr
        print("🟢 SIGNUP POST received:", request.form, file=sys.stderr)
        data = request.form

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
        current_year=datetime.date.today().year
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
        current_year=datetime.date.today().year
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
        current_year=datetime.date.today().year
    )

@bp.route("/shareview")
@login_required
def share():
    return render_template(
        "shareview.html",
        current_year=datetime.date.today().year
    )

@bp.route("/visualise")
@login_required
def visualise():
    return render_template(
        "visualise.html",
        current_year=datetime.date.today().year
    )

@bp.route("/frienddash")
@login_required
def frienddash():
    return render_template(
        "frienddash.html",
        current_year=datetime.date.today().year
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