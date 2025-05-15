# tests/test_models.py
import unittest
from app import create_app, db
from app.models import User, Friendship, FriendRequest, Podcast, PodcastLog,Like, Comment
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
        podcast = Podcast(name='Setup Podcast', spotify_id='setup123')
        db.session.add(podcast)
        db.session.commit()

        self.log = PodcastLog(
            user_id=self.user1.id,
            podcast_id=podcast.id,
            ep_name='Setup Episode',
            duration=1000
        )
        db.session.add(self.log)
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
    def test_like_creation(self):
        podcast = Podcast(name='Likeable Podcast', spotify_id='like123')
        db.session.add(podcast)
        db.session.commit()

        log = PodcastLog(user_id=self.user1.id, podcast_id=podcast.id, ep_name='Liked Episode', duration=1800)
        db.session.add(log)
        db.session.commit()

        like = Like(user_id=self.user2.id, post_id=log.id)
        db.session.add(like)
        db.session.commit()

        self.assertEqual(like.user_id, self.user2.id)
        self.assertEqual(like.post_id, log.id)
        self.assertTrue(isinstance(like.created_at, datetime))

    def test_like_uniqueness(self):
        podcast = Podcast(name='Unique Podcast', spotify_id='uniq123')
        db.session.add(podcast)
        db.session.commit()

        log = PodcastLog(user_id=self.user1.id, podcast_id=podcast.id, ep_name='Unique Episode', duration=1200)
        db.session.add(log)
        db.session.commit()

        like1 = Like(user_id=self.user2.id, post_id=log.id)
        like2 = Like(user_id=self.user2.id, post_id=log.id)
        db.session.add(like1)
        db.session.add(like2)

        with self.assertRaises(Exception):  # due to unique constraint
            db.session.commit()

    def test_comment_creation(self):
        podcast = Podcast(name='Commentable Podcast', spotify_id='cmt123')
        db.session.add(podcast)
        db.session.commit()

        log = PodcastLog(user_id=self.user1.id, podcast_id=podcast.id, ep_name='Commented Episode', duration=900)
        db.session.add(log)
        db.session.commit()

        comment = Comment(user_id=self.user2.id, post_id=log.id, text='Great episode!')
        db.session.add(comment)
        db.session.commit()

        self.assertEqual(comment.user_id, self.user2.id)
        self.assertEqual(comment.text, 'Great episode!')
        self.assertEqual(comment.post_id, log.id)

    def test_extended_podcast_log_fields(self):
        podcast = Podcast(name='Deep Podcast', spotify_id='deep999')
        db.session.add(podcast)
        db.session.commit()

        log = PodcastLog(
            user_id=self.user1.id,
            podcast_id=podcast.id,
            ep_name='Deep Episode',
            duration=4500,
            rating=4.5,
            platform='Spotify,Web',
            genre='Science',
            shared=True
        )
        db.session.add(log)
        db.session.commit()

        self.assertEqual(log.rating, 4.5)
        self.assertTrue(log.shared)
        self.assertIn('Spotify', log.platform)
        self.assertEqual(log.genre, 'Science')

    def test_comment_backref(self):
        podcast = Podcast(name='Backref Podcast', spotify_id='backref123')
        db.session.add(podcast)
        db.session.commit()

        log = PodcastLog(user_id=self.user1.id, podcast_id=podcast.id, ep_name='Backref Ep', duration=1000)
        db.session.add(log)
        db.session.commit()

        comment = Comment(user_id=self.user2.id, post_id=log.id, text='Interesting take!')
        db.session.add(comment)
        db.session.commit()

        user2_comments = self.user2.comments
        self.assertEqual(len(user2_comments), 1)
        self.assertEqual(user2_comments[0].text, 'Interesting take!')
    def test_friend_request_uniqueness(self):
        req1 = FriendRequest(from_user_id=self.user1.id, to_user_id=self.user2.id)
        db.session.add(req1)
        db.session.commit()

        req2 = FriendRequest(from_user_id=self.user1.id, to_user_id=self.user2.id)
        db.session.add(req2)
        with self.assertRaises(Exception):
            db.session.commit()

    def test_friend_request_status_change(self):
        req = FriendRequest(from_user_id=self.user1.id, to_user_id=self.user2.id)
        db.session.add(req)
        db.session.commit()

        req.status = 'accepted'
        db.session.commit()
        self.assertEqual(req.status, 'accepted')

    def test_friendship_creation(self):
        friendship = Friendship(user_id=self.user1.id, friend_id=self.user2.id)
        db.session.add(friendship)
        db.session.commit()
        self.assertIsNotNone(friendship.id)

    def test_friendship_uniqueness_constraint(self):
        db.session.add(Friendship(user_id=self.user1.id, friend_id=self.user2.id))
        db.session.commit()
        duplicate = Friendship(user_id=self.user1.id, friend_id=self.user2.id)
        db.session.add(duplicate)
        with self.assertRaises(Exception):
            db.session.commit()
    def test_comment_text_required(self):
        comment = Comment(user_id=self.user1.id, post_id=self.log.id, text=None)
        db.session.add(comment)
        with self.assertRaises(Exception):
            db.session.commit()



if __name__ == '__main__':
    unittest.main()