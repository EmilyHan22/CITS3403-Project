import os
from flask import Flask
from authlib.integrations.flask_client import OAuth
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail
from app.db import db

# ─── global extensions ──────────────────────────────────────
login_mgr = LoginManager()
bcrypt    = Bcrypt()
migrate   = Migrate()
mail      = Mail()
oauth     = OAuth()               # ← add this

def make_serializer(app):
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="password-reset")

def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates"
    )

    # ─── load all config from environment ────────────────────
    app.config.update({
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev"),
        "SQLALCHEMY_DATABASE_URI": (
            "sqlite:///" +
            os.path.join(os.path.abspath(os.path.dirname(__file__)), "podfolio.db")
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,

        "MAIL_SERVER":        os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT":          int(os.environ.get("MAIL_PORT", 587)),
        "MAIL_USE_TLS":       os.environ.get("MAIL_USE_TLS", "True") == "True",
        "MAIL_USERNAME":      os.environ.get("MAIL_USERNAME"),
        "MAIL_PASSWORD":      os.environ.get("MAIL_PASSWORD"),
        "MAIL_DEFAULT_SENDER":os.environ.get(
                                  "MAIL_DEFAULT_SENDER",
                                  f"Podfolio Support <{os.environ.get('MAIL_USERNAME')}>"
                              ),
        "SPOTIFY_CLIENT_ID": os.environ.get("SPOTIFY_CLIENT_ID"),
        "SPOTIFY_CLIENT_SECRET": os.environ.get("SPOTIFY_CLIENT_SECRET"),

        # ← your new Google OAuth creds
        "GOOGLE_CLIENT_ID":     os.environ.get("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET"),
    })


    # ─── OAuth: init + register Google ──────────────────────
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # ─── initialize the rest ───────────────────────────────
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_mgr.init_app(app)
    bcrypt.init_app(app)

    login_mgr.login_view = "main.login"

    @login_mgr.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # ─── register your blueprint ────────────────────────────
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # ─── no-cache headers ───────────────────────────────────
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
