from app.db import db
from app.models import User, Podcast, PodcastLo
import csv
import json


def init_db():
    """Initialize the database tables"""
    db.create_all()

def import_podcasts_from_csv(csv_path):
    """Import podcast data from CSV in the specified format"""
    with open(csv_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            podcast = Podcast(
                name=row['Name'],
                rating_volume=int(float(row['Rating_Volume'])),
                rating=float(row['Rating']),
                genre=row['Genre'],
                description=row['Description'],
                # Initialize predictive fields
                predicted_popularity=0.0,
                similar_to=json.dumps([])
            )
            db.session.add(podcast)
        db.session.commit()

def add_user(username, display_name=None):
    """Add a new user"""
    user = User(
        username=username,
        display_name=display_name or username
    )
    db.session.add(user)
    db.session.commit()
    return user


def log_podcast(user_id, podcast_id, duration, rating=None, notes=None, tags=None):
    """Log a podcast listening session"""
    log = PodcastLog(
        user_id=user_id,
        podcast_id=podcast_id,
        duration=duration,
        rating=rating,
        notes=notes,
        tags=tags
    )
    db.session.add(log)
    db.session.commit()
    return log

