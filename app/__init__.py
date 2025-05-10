from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail
from app.db import db
from authlib.integrations.flask_client import OAuth


# global extensions

login_mgr = LoginManager()
bcrypt    = Bcrypt()
migrate   = Migrate()
mail      = Mail()
oauth     = OAuth() 

def make_serializer(app):
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="password-reset")

def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates"
    )

    # Core settings
    app.config.update({
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev"),
        "SQLALCHEMY_DATABASE_URI": (
            "sqlite:///" +
            os.path.join(os.path.abspath(os.path.dirname(__file__)), "podfolio.db")
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    # Real Gmail SMTP settings using your 16-char App Password
    app.config.update({
        "MAIL_SERVER":       os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT":         int(os.environ.get("MAIL_PORT", 587)),
        "MAIL_USE_TLS":      os.environ.get("MAIL_USE_TLS", "True") == "True",
        "MAIL_USERNAME":     os.environ["MAIL_USERNAME"],            
        "MAIL_PASSWORD":     os.environ["MAIL_PASSWORD"],               
        "MAIL_DEFAULT_SENDER": os.environ.get(
            "MAIL_DEFAULT_SENDER",
            f"Podfolio Support <{os.environ['MAIL_USERNAME']}>"
        ),
    })

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_mgr.init_app(app)
    bcrypt.init_app(app)

    # ── Google OAuth config ─────────────────────────────────────
    app.config.update({
      "GOOGLE_CLIENT_ID":     os.environ["GOOGLE_CLIENT_ID"],
      "GOOGLE_CLIENT_SECRET": os.environ["GOOGLE_CLIENT_SECRET"],
    })

    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        # ← tell Authlib to fetch all endpoints (incl. jwks_uri) from here:
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
)


    login_mgr.login_view = "main.login"

    @login_mgr.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register your routes
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Prevent stale back-button caching
    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
