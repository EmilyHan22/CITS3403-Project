import os
import re
import secrets
import requests
from datetime import datetime, date
from urllib.parse import urlencode

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, jsonify, current_app
)
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError

from app import mail, make_serializer, oauth
from app.db import db
from app.models import User, Podcast, Friendship, PodcastLog

bp = Blueprint("main", __name__)

SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def is_password_strong(pw: str) -> bool:
    """True if pw has ≥8 chars, uppercase, lowercase, digit, and special."""
    return (
        len(pw) >= 8 and
        re.search(r"[A-Z]", pw) and
        re.search(r"[a-z]", pw) and
        re.search(r"\d", pw) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw)
    )


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))
    return render_template("index.html", current_year=date.today().year)


# ─── SIGN UP & LOGIN ─────────────────────────────────────────

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        cpw = request.form.get("confirm_password", "")

        # 1) Password match + strength
        if pw != cpw:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("main.signup"))
        if not is_password_strong(pw):
            flash("Password too weak.", "danger")
            return redirect(url_for("main.signup"))

        # 2) Duplicate email?
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("main.signup"))

        # 3) Generate a unique username from email prefix
        base = email.split("@")[0]
        uname = base
        counter = 1
        while User.query.filter_by(username=uname).first():
            uname = f"{base}{counter}"
            counter += 1

        # 4) Create & commit user
        user = User(username=uname, email=email, display_name=name)
        user.set_password(pw)
        user.auth_provider = "local"
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
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.auth_provider != 'local':
            flash('Please sign in with Google instead.', 'warning')
            return redirect(url_for('main.login'))
        if user and user.check_password(pw):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.podcast_log"))

        flash("Invalid credentials.", "danger")
        return redirect(url_for("main.login"))

    return render_template("login.html", current_year=date.today().year)


# ─── GOOGLE OAUTH ─────────────────────────────────────────────

@bp.route("/login/google")
def login_google():
    redirect_uri = url_for("main.auth_google", _external=True)
    try:
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"OAuth metadata fetch failed: {e}")
        flash("Authentication service unavailable. Please try again later.", "danger")
        return redirect(url_for("main.login"))


@bp.route("/auth/google")
def auth_google():
    try:
        token = oauth.google.authorize_access_token()
        ui_endpoint = oauth.google.server_metadata["userinfo_endpoint"]
        resp = oauth.google.get(ui_endpoint)
        user_info = resp.json()
    except Exception as e:
        current_app.logger.error(f"OAuth network error: {e}")
        flash("Authentication service unavailable. Please try again later.", "danger")
        return redirect(url_for("main.login"))

    if not user_info.get("email") or not user_info.get("email_verified"):
        flash("Google email not verified—please use a verified Google account.", "danger")
        return redirect(url_for("main.login"))

    email = user_info["email"].lower()
    user = User.query.filter_by(email=email).first()

    user = User.query.filter_by(email=email).first()
    if user and user.auth_provider != 'google':
        flash('That email was registered with a password. Please log in with email & password.', 'warning')
        return redirect(url_for('main.login'))

    if not user:
        # First-time Google signup
        uname = email.split("@")[0]
        counter = 1
        while User.query.filter_by(username=uname).first():
            uname = f"{email.split('@')[0]}{counter}"
            counter += 1

        user = User(
            username=uname,
            email=email,
            display_name=user_info.get("name")
        )
        user.auth_provider = "google"
        dummy_pw = secrets.token_urlsafe(16)
        user.set_password(dummy_pw)
        db.session.add(user)
        db.session.commit()
    else:
        # Existing user → sync display_name
        user.display_name = user_info.get("name")
        db.session.commit()

    login_user(user)
    return redirect(url_for("main.podcast_log"), code=303)


# ─── PASSWORD RESET ──────────────────────────────────────────

@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.podcast_log"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email address isn’t registered.", "danger")
            return redirect(url_for("main.forgot_password"))

        token = make_serializer(current_app).dumps(user.email)
        link = url_for("main.reset_password", token=token, _external=True)
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


# ─── SETTINGS & DELETE ACCOUNT ───────────────────────────────

@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        form = request.form
        # Display name
        new_display = form.get("display_name", "").strip()
        if new_display and new_display != current_user.display_name:
            current_user.display_name = new_display
        # Email
        new_email = form.get("email", "").strip().lower()
        if new_email and new_email != current_user.email:
            if User.query.filter_by(email=new_email).first():
                flash("That email is already taken.", "warning")
            else:
                current_user.email = new_email
        # Password change
        pw = form.get("current_password", "")
        new_pw = form.get("new_password", "")
        cpw = form.get("confirm_new_password", "")
        if pw or new_pw or cpw:
            if not current_user.check_password(pw):
                flash("Current password is incorrect.", "danger")
            elif new_pw != cpw:
                flash("New passwords do not match.", "danger")
            elif not is_password_strong(new_pw):
                flash("New password too weak.", "danger")
            else:
                current_user.set_password(new_pw)
                flash("Password updated.", "success")

        # Commit all changes
        try:
            db.session.commit()
            flash("Settings saved.", "success")
        except SQLAlchemyError as e:
            current_app.logger.error(f"Settings save failed: {e}")
            db.session.rollback()
            flash("Failed to save settings. Try again later.", "danger")

        return redirect(url_for("main.settings"))

    return render_template("settings.html", user=current_user)


@bp.route("/settings/delete_account", methods=["POST"])
@login_required
def delete_account():
    confirm = request.form.get("confirmation", "")
    if confirm != "DELETE":
        flash("You must type DELETE to confirm account deletion.", "danger")
        return redirect(url_for("main.settings"))
    try:
        PodcastLog.query.filter_by(user_id=current_user.id).delete()
        Friendship.query.filter_by(user_id=current_user.id).delete()
        Friendship.query.filter_by(friend_id=current_user.id).delete()
        user = current_user._get_current_object()
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash("Your account has been deleted.", "success")
        return redirect(url_for("main.index"))
    except Exception as e:
        current_app.logger.error(f"Error deleting account: {e}")
        db.session.rollback()
        flash("Unable to delete account. Please try again later.", "danger")
        return redirect(url_for("main.settings"))


# ─── PODCAST & FRIENDSHIP ROUTES ────────────────────────────

@bp.route("/podcast-log", methods=["GET", "POST"])
@login_required
def podcast_log():
    if request.method == "POST":
        # TODO: handle form submission
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


@bp.route("/add_friend", methods=["POST"])
@login_required
def add_friend():
    username = request.json.get("username")
    friend = User.query.filter_by(username=username).first()
    if not friend:
        return jsonify({"error": "User not found"}), 404
    if current_user.id == friend.id:
        return jsonify({"error": "Cannot add yourself"}), 400
    if Friendship.query.filter_by(user_id=current_user.id, friend_id=friend.id).first():
        return jsonify({"error": "Already friends"}), 400
    friendship = Friendship(user_id=current_user.id, friend_id=friend.id)
    db.session.add(friendship)
    db.session.commit()
    return jsonify({
        "message": f"Added {username} as friend",
        "friend": {"id": friend.id, "username": friend.username}
    })


@bp.route("/remove_friend/<int:friend_id>", methods=["DELETE"])
@login_required
def remove_friend(friend_id):
    friendship = Friendship.query.filter_by(
        user_id=current_user.id, friend_id=friend_id
    ).first()
    if not friendship:
        return jsonify({"error": "Not currently following this user"}), 404
    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"message": "Removed from your following"})


@bp.route("/search_podcast_names")
@login_required
def search_podcast_names():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    results = Podcast.query.filter(Podcast.name.ilike(f"%{q}%"))\
        .with_entities(Podcast.id, Podcast.name).limit(10).all()
    return jsonify([{"id": p.id, "name": p.name} for p in results])


@bp.route("/log_podcast", methods=["POST"])
@login_required
def log_podcast():
    if not request.is_json:
        return jsonify({"success": False, "message": "Invalid content type"}), 400
    data = request.get_json()
    if not data.get("podcast_id"):
        return jsonify({"success": False, "message": "Podcast is required"}), 400
    try:
        podcast = Podcast.query.filter_by(spotify_id=data["podcast_id"]).first()
        if not podcast:
            token = get_spotify_token()
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"https://api.spotify.com/v1/shows/{data['podcast_id']}", headers=headers)
            show = resp.json()
            podcast = Podcast(
                spotify_id=show["id"],
                name=show["name"],
                description=show["description"]
            )
            db.session.add(podcast)
            db.session.commit()
        log = PodcastLog(
            user_id=current_user.id,
            podcast_id=podcast.id,
            notes=data.get("episode"),
            tags=data.get("platform"),
            duration=(int(data.get("duration")) * 60) if data.get("duration") else None,
            rating=float(data["rating"]) if data.get("rating") else None
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({"success": True, "message": "Podcast logged successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error logging podcast: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    resp = requests.post(
        auth_url,
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    return resp.json().get("access_token")


@bp.route("/search_spotify_podcasts")
@login_required
def search_spotify_podcasts():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        token = get_spotify_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": q, "type": "show", "market": "US", "limit": 10}
        resp = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
        shows = resp.json().get("shows", {}).get("items", [])
        return jsonify([
            {
                "id": s["id"],
                "name": s["name"],
                "publisher": s["publisher"],
                "image": s["images"][0]["url"] if s["images"] else None
            }
            for s in shows
        ])
    except Exception as e:
        current_app.logger.error(f"Spotify search error: {e}")
        return jsonify([])


@bp.route("/callback")
def spotify_callback():
    # Placeholder for OAuth callback handling if you implement it
    return redirect(url_for("main.podcast_log"))
