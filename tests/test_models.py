# tests/test_models.py
import unittest
from app import create_app, db
from app.models import User, Friendship, FriendRequest, Podcast, PodcastLog
from datetime import datetime

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.user1 = User(
            username='testuser1', 
            email='test1@example.com',
            pw_hash='dummyhash',
            display_name='Test User 1'
        )
        self.user2 = User(
            username='testuser2', 
            email='test2@example.com',
            pw_hash='dummyhash',
            display_name='Test User 2'
        )
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        self.assertEqual(self.user1.username, 'testuser1')
        self.assertEqual(self.user1.email, 'test1@example.com')
        self.assertTrue(isinstance(self.user1.created_at, datetime))

    def test_password_hashing(self):
        self.user1.set_password('testpassword')
        self.assertTrue(self.user1.check_password('testpassword'))
        self.assertFalse(self.user1.check_password('wrongpassword'))

    def test_friendship_creation(self):
        friendship = Friendship(user_id=self.user1.id, friend_id=self.user2.id)
        db.session.add(friendship)
        db.session.commit()
        
        self.assertEqual(friendship.user_id, self.user1.id)
        self.assertEqual(friendship.friend_id, self.user2.id)
        self.assertTrue(isinstance(friendship.created_at, datetime))

    def test_friend_request_creation(self):
        fr = FriendRequest(
            from_user_id=self.user1.id,
            to_user_id=self.user2.id,
            status='pending'
        )
        db.session.add(fr)
        db.session.commit()
        
        self.assertEqual(fr.from_user_id, self.user1.id)
        self.assertEqual(fr.to_user_id, self.user2.id)
        self.assertEqual(fr.status, 'pending')

    def test_podcast_creation(self):
        podcast = Podcast(
            name='Test Podcast',
            spotify_id='12345',
            description='A test podcast'
        )
        db.session.add(podcast)
        db.session.commit()
        
        self.assertEqual(podcast.name, 'Test Podcast')
        self.assertEqual(podcast.spotify_id, '12345')

    def test_podcast_log_creation(self):
        podcast = Podcast(
            name='Test Podcast',
            spotify_id='12345'
        )
        db.session.add(podcast)
        db.session.commit()
        
        log = PodcastLog(
            user_id=self.user1.id,
            podcast_id=podcast.id,
            ep_name='Test Episode',
            duration=3600
        )
        db.session.add(log)
        db.session.commit()
        
        self.assertEqual(log.user_id, self.user1.id)
        self.assertEqual(log.podcast_id, podcast.id)
        self.assertEqual(log.ep_name, 'Test Episode')

if __name__ == '__main__':
    unittest.main()