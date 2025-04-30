from app import create_app
from app.load_data import load_podcast_data

app = create_app()

with app.app_context():
    load_podcast_data()
