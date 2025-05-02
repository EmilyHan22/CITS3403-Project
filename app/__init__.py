import os
from flask import Flask
from flask_migrate import Migrate
from app.db import db
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from app.models import User


# global extensions
login_mgr = LoginManager()
bcrypt    = Bcrypt()
migrate   = Migrate()


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates"
    )
    # Secret key for sessions; override in instance/config.py if needed
    app.config.from_mapping(SECRET_KEY="dev")

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'podfolio.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_mgr.init_app(app)
    bcrypt.init_app(app)

    login_mgr.login_view = "main.login"

    @login_mgr.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        from app.models import Podcast, User, PodcastLog
        db.create_all()


     # where to redirect if login_required fails
    login_mgr.login_view = "main.login"



    # simple route blueprint

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, "
            "private, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
