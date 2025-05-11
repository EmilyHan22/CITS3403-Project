import os
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, jsonify, current_app
)
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from app import mail, make_serializer, oauth
from flask_login import (
    login_user, logout_user,
    current_user, login_required
)
from app.db import db
from app.models import User, Podcast, Friendship, PodcastLog
from datetime import datetime, date
import sys

bp = Blueprint("main", __name__)

# ── Google Login ──────────────────────────────────────────────────
@bp.route("/login/google")
def login_google():
    redirect_uri = url_for("main.authorize", _external=True)
    return oauth.google.authorize_redirect(        redirect_uri=redirect_uri,
        prompt="select_account",          # force account picker
        access_type="offline",            # request refresh tokens
        include_granted_scopes="true"     # retain previous scopes
    )

@bp.route("/authorize")
def authorize():
    # 1) Handle user denying or OAuth errors
    if request.args.get("error"):
        flash("Google sign-in was cancelled or failed.", "warning")
        return redirect(url_for("main.login"))

    # 2) Exchange code for tokens (validate CSRF state)
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        current_app.logger.error("Google OAuth token exchange failed", exc_info=e)
        flash("Google login failed. Please try again.", "danger")
        return redirect(url_for("main.login"))

    # 3) Fetch user info from Google
    try:
        userinfo_endpoint = oauth.google.server_metadata["userinfo_endpoint"]
        resp = oauth.google.get(userinfo_endpoint)
        resp.raise_for_status()
        user_info = resp.json()
    except Exception as e:
        current_app.logger.error("Failed to fetch Google userinfo", exc_info=e)
        flash("Could not retrieve your Google profile. Please try again.", "danger")
        return redirect(url_for("main.login"))

    # 4) Reject unverified Google emails
    verified = user_info.get("verified_email") or user_info.get("email_verified")
    if not verified:
        flash(
            "Your Google account email isn’t verified. "
            "Please verify it with Google first.",
            "warning"
        )
        return redirect(url_for("main.login"))

    # 5) Lookup by Google ID
    sub = user_info["sub"]
    user_by_google = User.query.filter_by(google_id=sub).first()
    if user_by_google:
        login_user(user_by_google)
        return redirect(url_for("main.podcast_log"))

    # 6) Merge into existing email user
    email = user_info.get("email")
    user_by_email = User.query.filter_by(email=email).first()
    if user_by_email:
        user_by_email.google_id = sub
        db.session.commit()
        login_user(user_by_email)
        return redirect(url_for("main.podcast_log"))

    # 7) Create a new user record
    user = User(
        username     = email.split("@")[0],
        email        = email,
        display_name = user_info.get("name", ""),
        google_id    = sub
    )
    # set a random unusable password
    user.set_password(os.urandom(16).hex())
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for("main.podcast_log"))

# ── Password Reset ────────────────────────────────────────────
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

        flash("If that email is registered, you’ll receive a reset link shortly.", "info")
        return redirect(url_for("main.login"))

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
        cpw    = request.form.get("confirm_password", "")
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
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))
    return render_template(
        "index.html",
        current_year=date.today().year
    )

@bp.route("/signup", methods=["GET", "POST"] )
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        data = request.form
        if data.get("password") != data.get("confirm_password"):
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.signup"))
        if User.query.filter_by(username=data["username"]).first():
            flash("Username already taken.", "warning")
            return redirect(url_for("main.signup"))
        if User.query.filter_by(email=data["email"]).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("main.signup"))

        user = User(
            username     = data["username"],
            email        = data["email"],
            display_name = f"{data['first_name']} {data['last_name']}"
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("main.podcast_log"))

    return render_template("signup.html", current_year=date.today().year)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        email    = request.form.get("email", "")
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.podcast_log"))
        flash("Invalid credentials.", "danger")
        return redirect(url_for("main.login"))

    return render_template("login.html", current_year=date.today().year)

# ─── Protected routes ─────────────────────────────────────────
@bp.route("/podcast-log", methods=["GET", "POST"])
@login_required
def podcast_log():
    if request.method == "POST":
        return redirect(url_for("main.podcast_log"))
    return render_template("PodcastLog.html", current_year=date.today().year)

@bp.route("/shareview")
@login_required
def share():
    return render_template("shareview.html", current_year=date.today().year)

@bp.route("/visualise")
@login_required
def visualise():
    return render_template("visualise.html", current_year=date.today().year)

@bp.route("/frienddash")
@login_required
def frienddash():
    return render_template("frienddash.html", current_year=date.today().year)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

# ── Friendships & Podcasts API ─────────────────────────────────
@bp.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    username = request.json.get('username')
    friend = User.query.filter_by(username=username).first()
    if not friend:
        return jsonify({'error': 'User not found'}), 404
    if current_user.id == friend.id:
        return jsonify({'error': 'Cannot add yourself'}), 400
    existing = Friendship.query.filter_by(
        user_id=current_user.id,
        friend_id=friend.id
    ).first()
    if existing:
        return jsonify({'error': 'Already friends'}), 400
    friendship = Friendship(user_id=current_user.id, friend_id=friend.id)
    db.session.add(friendship)
    db.session.commit()
    return jsonify({'message': f'Added {username} as friend', 'friend': {'id': friend.id, 'username': friend.username}})

@bp.route('/remove_friend/<int:friend_id>', methods=['DELETE'])
@login_required
def remove_friend(friend_id):
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
    if not data.get('podcast_id'):
        return jsonify({'success': False, 'message': 'Podcast is required'}), 400
    try:
        podcast_log = PodcastLog(
            user_id=current_user.id,
            podcast_id=data['podcast_id'],
            notes=data.get('episode'),
            tags=data.get('platform'),
            duration=(int(data.get('duration')) * 60) if data.get('duration') else None,
            rating=float(data['rating']) if data.get('rating') else None
        )
        db.session.add(podcast_log)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Podcast logged successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error logging podcast: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
