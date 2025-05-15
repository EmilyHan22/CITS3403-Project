from app.db import db
from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import synonym
bcrypt = Bcrypt()


class User(db.Model, UserMixin):
    """User accounts with email & password hash for authentication."""
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(64), unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    pw_hash      = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(64))
    auth_provider = db.Column(
        db.String(20),
        nullable=False,
        default='local'
    )
    profile_pic = db.Column(
        db.String(255),
        nullable=False,
        default='default.png'
    )
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

# People I've added
    friends_added = db.relationship(
        'Friendship',
        foreign_keys='Friendship.user_id',
        backref=db.backref('adder', lazy='joined'),
        lazy='dynamic'
    )
    
    # People who added me
    added_by = db.relationship(
        'Friendship',
        foreign_keys='Friendship.friend_id',
        backref=db.backref('added_friend', lazy='joined'),
        lazy='dynamic'
    )
    
    @property
    def people_i_added(self):
        """Users I've added to my friends list"""
        return User.query.join(Friendship, User.id == Friendship.friend_id)\
                        .filter(Friendship.user_id == self.id)
    
    @property
    def people_added_me(self):
        """Users who have me in their friends list"""
        return User.query.join(Friendship, User.id == Friendship.user_id)\
                        .filter(Friendship.friend_id == self.id)

    def set_password(self, password):
        # bcrypt imported below
        self.pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.pw_hash, password)
    
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )
class FriendRequest(db.Model):
    """Tracks pending friend requests between users."""
    __tablename__ = 'friend_request'

    id           = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status       = db.Column(db.String(20), nullable=False, default='pending')  # pending/accepted/rejected
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('from_user_id', 'to_user_id', name='uq_friend_request'),
    )

    # “Official” relationships
    requester = db.relationship(
        'User',
        foreign_keys=[from_user_id],
        backref=db.backref('requests_sent', lazy='dynamic')
    )
    requestee = db.relationship(
        'User',
        foreign_keys=[to_user_id],
        backref=db.backref('requests_received', lazy='dynamic')
    )

    # Aliases so templates can do r.from_user / r.to_user
    from_user = synonym('requester')
    to_user   = synonym('requestee')



class Podcast(db.Model):
    __tablename__ = 'podcast'  # Explicit table name
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    spotify_id = db.Column(db.String(120), unique=True)  # Spotify's ID
    rating_volume = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre = db.Column(db.String(64))
    description = db.Column(db.Text)
    publisher = db.Column(db.String(120))
    image_url = db.Column(db.String(255))
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
    ep_name = db.Column(db.Text)
    platform = db.Column(db.String(200))  # comma-separated tags
    genre = db.Column(db.String(64))
    # Relationship
    podcast = db.relationship('Podcast', backref='logs')