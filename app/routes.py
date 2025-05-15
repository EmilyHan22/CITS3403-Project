import os
import re
import secrets
import requests
from datetime import datetime, date
from urllib.parse import urlencode

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, jsonify, current_app, abort
)
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_

from app import mail, make_serializer, oauth
from app.db import db
from app.models import User, Podcast, Friendship, PodcastLog, FriendRequest, Like, Comment
from werkzeug.utils import secure_filename

ALLOWED_EXT = {'png','jpg','jpeg','gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

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

@bp.route('/search')
@login_required
def search():
    # just render the blank search page
    return render_template('search.html', current_year=date.today().year)

@bp.route("/profile/<username>")
@login_required
def profile(username):
    # 1) find the user
    profile_user = User.query.filter_by(username=username).first_or_404()

    # 2) determine whether current_user is allowed
    is_owner  = profile_user.id == current_user.id
    is_friend = Friendship.query.filter_by(
                    user_id=current_user.id,
                    friend_id=profile_user.id
                ).first() is not None

    # 3) fetch counts & logs (we'll still fetch logs but template will gate display)
    followers_count = profile_user.people_added_me.count()
    following_count = profile_user.people_i_added.count()
    logs = (
        PodcastLog.query
        .filter_by(user_id=profile_user.id)
        .order_by(PodcastLog.listened_at.desc())
        .all()
    )

    return render_template(
        "profile.html",
        profile_user=profile_user,
        followers_count=followers_count,
        following_count=following_count,
        logs=logs,
        is_owner=is_owner,
        is_friend=is_friend
    )



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
        pic = request.files.get('profile_pic')
        if pic and allowed_file(pic.filename):
            filename = secure_filename(pic.filename)
            filename = f"{user.username}_{secrets.token_hex(8)}_{filename}"
            pic.save(os.path.join(
                current_app.root_path,
                'static/uploads',
                filename
            ))
            user.profile_pic = filename
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
        pic = request.files.get('profile_pic')
        if pic and allowed_file(pic.filename):
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(pic.filename)
            filename = f"{current_user.username}_{secrets.token_hex(8)}_{filename}"
            path = os.path.join(upload_dir, filename)
            pic.save(path)
            current_user.profile_pic = filename

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


@bp.route('/shareview')
@login_required
def shareview():
    page     = request.args.get('page', 1, type=int)
    per_page = 9
    pagination = PodcastLog.query \
        .filter_by(shared=True) \
        .order_by(PodcastLog.listened_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('shareview.html', pagination=pagination)

# at the top of routes.py
from flask import url_for

from app.models import Comment, Like  # <-- import your Comment and Like models

@bp.route('/api/share_posts')
@login_required
def api_share_posts():
    page, per_page = request.args.get('page',1,type=int), 9
    pagination = PodcastLog.query\
        .filter_by(shared=True)\
        .order_by(PodcastLog.listened_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for log in pagination.items:
        # pull poster
        poster = User.query.get(log.user_id)

        # pull likes
        total_likes = Like.query.filter_by(post_id=log.id).count()
        liked       = Like.query.filter_by(post_id=log.id, user_id=current_user.id).first() is not None

        # pull comments
        raw_comments = Comment.query\
            .filter_by(post_id=log.id)\
            .order_by(Comment.created_at.asc())\
            .all()
        comments = [
            {
              'commenter': c.user.display_name or c.user.username,
              'text':      c.text
            }
            for c in raw_comments
        ]

        posts.append({
          'id':              log.id,
          'podcast_name':    log.podcast.name,
          'podcast_image':   log.podcast.image_url,
          'ep_name':         log.ep_name,
          'platform':        log.platform,
          'duration_min':    (log.duration / 60) if log.duration else None,
          'genre':           log.podcast.genre,
          'rating':          log.rating,
          'poster_username': poster.username,
          'poster_pic':      url_for('static', filename='uploads/' + poster.profile_pic),
          'likes':           total_likes,
          'liked':           liked,
          'comments':        comments
        })

    return jsonify({
      'posts':    posts,
      'next_page': pagination.next_num if pagination.has_next else None
    })


@bp.route('/share_podcast/<int:log_id>', methods=['POST'])
@login_required
def share_podcast(log_id):
    log = PodcastLog.query.get_or_404(log_id)
    # only the owner can share their own log
    if log.user_id != current_user.id:
        abort(403)
    log.shared = True
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/posts/<int:post_id>/like', methods=['POST', 'DELETE'])
@login_required
def toggle_like(post_id):
    # POST   → add like
    # DELETE → remove like
    log = PodcastLog.query.get_or_404(post_id)
    existing = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if request.method == 'POST' and not existing:
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
    elif request.method == 'DELETE' and existing:
        db.session.delete(existing)
    db.session.commit()

    # return new count
    count = Like.query.filter_by(post_id=post_id).count()
    return jsonify({ 'success': True, 'likes': count })


@bp.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def post_comment(post_id):
    log = PodcastLog.query.get_or_404(post_id)
    data = request.get_json() or {}
    text = data.get('text','').strip()
    if not text:
        return jsonify({ 'success': False }), 400

    comment = Comment(
      user_id    =current_user.id,
      post_id    =post_id,
      text       =text,
      created_at =datetime.utcnow()
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({
      'success':   True,
      'commenter': current_user.username,
      'text':      text
    })




@bp.route("/visualise")
@login_required
def visualise():
    return render_template("visualise.html", current_year=date.today().year)


@bp.route("/frienddash")
@login_required
def frienddash():
    return render_template("frienddash.html", current_year=date.today().year)



@bp.route('/friends')
@login_required
def friends():
    # Pending *sent* requests
    sent_requests = (
        FriendRequest.query
        .filter_by(from_user_id=current_user.id, status='pending')
        .order_by(FriendRequest.created_at.desc())
        .all()
    )
    # Pending *received* requests
    received_requests = (
        FriendRequest.query
        .filter_by(to_user_id=current_user.id, status='pending')
        .order_by(FriendRequest.created_at.desc())
        .all()
    )
    # Already-accepted friendships
    friends_list = (
        User.query
        .join(Friendship, User.id == Friendship.friend_id)
        .filter(Friendship.user_id == current_user.id)
        .all()
    )
    return render_template(
        'friends.html',
        sent_requests=sent_requests,
        received_requests=received_requests,
        friends=friends_list
    )


from sqlalchemy import or_

from sqlalchemy import or_

@bp.route('/search_users')
@login_required
def search_users():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    matches = (
        User.query
            .filter(
                or_(
                    User.username.ilike(f'%{q}%'),
                    User.display_name.ilike(f'%{q}%')
                ),
                User.id != current_user.id
            )
            .with_entities(User.username)
            .limit(10)
            .all()
    )
    return jsonify([u.username for u in matches])



@bp.route('/send_friend_request', methods=['POST'])
@login_required
def send_friend_request():
    data     = request.get_json() or {}
    username = (data.get('username') or '').strip()

    # 1) find the target user
    friend = User.query.filter_by(username=username).first()
    if not friend:
        return jsonify({'error': 'User not found'}), 404

    # 2) no self-requests
    if friend.id == current_user.id:
        return jsonify({'error': 'Cannot add yourself'}), 400

    # 3) check for any existing FriendRequest between these two
    existing = FriendRequest.query.filter_by(
        from_user_id=current_user.id,
        to_user_id=friend.id
    ).first()

    if existing:
        if existing.status == 'pending':
            return jsonify({'error': 'Already friends or request pending'}), 400
        elif existing.status == 'rejected':
            # resurrect the old request
            existing.status     = 'pending'
            existing.created_at = datetime.utcnow()
            try:
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Friend request re-sent to {username}',
                    'request': {'id': existing.id, 'to_user': username}
                }), 201
            except Exception as e:
                current_app.logger.error(f"Error re-sending friend request: {e}")
                db.session.rollback()
                return jsonify({'error': 'Could not send friend request'}), 500
        else:  # status == 'accepted'
            return jsonify({'error': 'Already friends'}), 400

    # 4) ensure they’re not already friends (via the Friendship table)
    already_friends = Friendship.query.filter_by(
        user_id=current_user.id,
        friend_id=friend.id
    ).first()
    if already_friends:
        return jsonify({'error': 'Already friends'}), 400

    # 5) create & commit a fresh FriendRequest
    fr = FriendRequest(
        from_user_id=current_user.id,
        to_user_id  =friend.id,
        status      ='pending'
    )
    try:
        db.session.add(fr)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Friend request sent to {username}',
            'request': {'id': fr.id, 'to_user': username}
        }), 201

    except Exception as e:
        current_app.logger.error(f"Error sending friend request: {e}")
        db.session.rollback()
        return jsonify({'error': 'Could not send friend request'}), 500




@bp.route('/respond_friend_request', methods=['POST'])
@login_required
def respond_friend_request():
    data     = request.get_json() or {}
    req_id   = data.get('request_id')
    action   = data.get('action')  # 'accept' or 'reject'

    # 1) fetch & guard
    fr = FriendRequest.query.get(req_id)
    if not fr or fr.to_user_id != current_user.id:
        return jsonify({'error': 'Invalid request'}), 400
    if action not in ('accept', 'reject'):
        return jsonify({'error': 'Invalid action'}), 400

    # 2) update status
    fr.status = action
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error responding to friend request: {e}")
        db.session.rollback()
        return jsonify({'error': 'Could not respond to request'}), 500

    # 3) if accepted, create mutual friendships
    if action == 'accept':
        try:
            # add both directions
            db.session.add_all([
                Friendship(user_id=fr.from_user_id, friend_id=fr.to_user_id),
                Friendship(user_id=fr.to_user_id,   friend_id=fr.from_user_id)
            ])
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error creating friendships: {e}")
            db.session.rollback()
            return jsonify({'error': 'Could not create friendships'}), 500

    return jsonify({'success': True}), 200





@bp.route('/remove_friend/<int:friend_id>', methods=['DELETE'])
@login_required
def remove_friend(friend_id):
    # 1) Remove the mutual friendships
    fwd = Friendship.query.filter_by(
        user_id=current_user.id,
        friend_id=friend_id
    ).first()
    rev = Friendship.query.filter_by(
        user_id=friend_id,
        friend_id=current_user.id
    ).first()

    if not fwd:
        return jsonify({'error': 'Not friends'}), 404

    db.session.delete(fwd)
    if rev:
        db.session.delete(rev)

    # 2) Also delete any FriendRequest between you and that user
    FriendRequest.query.filter(
        or_(
            and_(
                FriendRequest.from_user_id == current_user.id,
                FriendRequest.to_user_id   == friend_id
            ),
            and_(
                FriendRequest.from_user_id == friend_id,
                FriendRequest.to_user_id   == current_user.id
            )
        )
    ).delete(synchronize_session=False)

    # 3) Commit everything in one go
    db.session.commit()

    return jsonify({'success': True})


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))



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
            ep_name=data.get("episode"),
            platform=data.get("platform"),
            duration=(int(data.get("duration")) * 60) if data.get("duration") else None,
            rating=float(data["rating"]) if data.get("rating") else None,
            genre=data.get("genre") 

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