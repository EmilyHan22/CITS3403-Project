import os
from flask import Flask

def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates"
    )
    # Secret key for sessions; override in instance/config.py if needed
    app.config.from_mapping(SECRET_KEY="dev")
    # simple route blueprint
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
