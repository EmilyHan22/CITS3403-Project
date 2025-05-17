from app import create_app, db
from app.models import (
    User, Friendship, FriendRequest,
    Podcast, PodcastLog, Like, Comment,
    Conversation, Message
)
from faker import Faker
import random
from itertools import combinations

def seed():
    app = create_app()
    with app.app_context():
        # Recreate the database
        db.drop_all()
        db.create_all()

        faker = Faker()
        users = []
        # Create 10 users
        for _ in range(10):
            u = User(
                username=faker.unique.user_name(),
                email=faker.unique.email(),
                display_name=faker.name()
            )
            u.set_password('password123')
            db.session.add(u)
            users.append(u)
        db.session.commit()

        user_ids = [u.id for u in users]

        # Create accepted friendships: pick 10 unique pairs
        pairs = list(combinations(user_ids, 2))
        accepted = random.sample(pairs, min(10, len(pairs)))
        for u1, u2 in accepted:
            db.session.add(Friendship(user_id=u1, friend_id=u2))
            db.session.add(Friendship(user_id=u2, friend_id=u1))
        db.session.commit()

        # Create pending friend requests (outgoing)
        for user in users:
            others = [o for o in users if o.id != user.id]
            # Two random targets per user
            targets = random.sample(others, min(2, len(others)))
            for tgt in targets:
                # avoid duplicate or accepted
                if Friendship.query.filter_by(user_id=user.id, friend_id=tgt.id).first():
                    continue
                existing = FriendRequest.query.filter_by(
                    from_user_id=user.id, to_user_id=tgt.id
                ).first()
                if not existing:
                    fr = FriendRequest(
                        from_user_id=user.id,
                        to_user_id=tgt.id,
                        status='pending'
                    )
                    db.session.add(fr)
        db.session.commit()

        # Create 10 podcasts
        podcasts = []
        genres = ['Tech', 'Business', 'Comedy', 'News', 'Education']
        for _ in range(10):
            p = Podcast(
                name=faker.catch_phrase(),
                spotify_id=faker.unique.uuid4(),
                rating_volume=random.randint(1, 1000),
                rating=round(random.uniform(1, 5), 1),
                genre=random.choice(genres),
                description=faker.text(max_nb_chars=200),
                publisher=faker.company(),
                image_url=faker.image_url(),
                predicted_popularity=round(random.random(), 2),
                similar_to='[]'
            )
            db.session.add(p)
            podcasts.append(p)
        db.session.commit()

        # Create logs spread over 8 weeks
        logs = []
        for user in users:
            for _ in range(random.randint(5, 20)):
                podcast = random.choice(podcasts)
                log = PodcastLog(
                    user_id=user.id,
                    podcast_id=podcast.id,
                    listened_at=faker.date_time_between(start_date='-8w', end_date='now'),
                    duration=random.randint(60, 3600),
                    rating=random.choice([1, 2, 3, 4, 5]),
                    ep_name=faker.sentence(nb_words=4),
                    platform=random.choice(['Web', 'Mobile', 'Podcast App']),
                    genre=podcast.genre,
                    review=(faker.text(max_nb_chars=100) if random.random() < 0.7 else None),
                    shared=random.choice([True, False])
                )
                db.session.add(log)
                logs.append(log)
        db.session.commit()

        # Likes & comments for logs
        for log in random.sample(logs, min(len(logs), 20)):
            liker = random.choice([u for u in users if u.id != log.user_id])
            db.session.add(Like(user_id=liker.id, post_id=log.id))
        db.session.commit()

        for _ in range(10):
            log = random.choice(logs)
            commenter = random.choice([u for u in users if u.id != log.user_id])
            db.session.add(Comment(
                user_id=commenter.id,
                post_id=log.id,
                text=faker.sentence()
            ))
        db.session.commit()

        # Create conversations & messages
        conv_pairs = random.sample(pairs, min(10, len(pairs)))
        for u1, u2 in conv_pairs:
            conv = Conversation(user1_id=u1, user2_id=u2)
            db.session.add(conv)
            db.session.commit()
            for _ in range(random.randint(1, 5)):
                sender, recipient = ( (u1, u2) if random.choice([True, False]) else (u2, u1) )
                db.session.add(Message(
                    conversation_id=conv.id,
                    sender_id=sender,
                    recipient_id=recipient,
                    text=faker.sentence(),
                    podcast_log_id=(random.choice(logs).id if random.random() < 0.3 else None),
                    read=random.choice([True, False])
                ))
            db.session.commit()

        print("Seed data added successfully.")

if __name__ == '__main__':
    seed()