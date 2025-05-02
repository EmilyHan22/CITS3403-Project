import os
from flask import Flask
from app.db import db




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
    with app.app_context():
        from app.models import Podcast, User, PodcastLog
        db.create_all()



    # simple route blueprint

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
