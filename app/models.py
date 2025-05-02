from app.db import db
from datetime import datetime


class User(db.Model):
    """User accounts without login functionality (for now)"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    


class Podcast(db.Model):
    __tablename__ = 'podcast'  # Explicit table name
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    rating_volume = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre = db.Column(db.String(64))
    description = db.Column(db.Text)
    predicted_popularity = db.Column(db.Float, default=0.0)
    similar_to = db.Column(db.String(200))  # JSON string
    


class PodcastLog(db.Model):
    """User podcast listening logs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    podcast_id = db.Column(db.Integer, db.ForeignKey('podcast.id'))
    listened_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer)  # in seconds
    rating = db.Column(db.Float)  # 1-5 scale
    notes = db.Column(db.Text)
    tags = db.Column(db.String(200))  # comma-separated tags
    
    # Relationship
    podcast = db.relationship('Podcast', backref='logs')