import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.models import User, Podcast
from werkzeug.security import generate_password_hash
import threading
import time
from werkzeug.serving import make_server
import tempfile
import os


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()
        self.ctx.pop()


class SeleniumTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create temp file for SQLite db that is accessible across threads
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='.sqlite')
    
    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        os.unlink(cls.db_path)  # Remove temp db file
    
    def setUp(self):
        # Update config before app creation
        self.app = create_app()
        self.app.config.update({
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.db_path}',
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SERVER_NAME': 'localhost:5000'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create user for login tests
        self.user = User(
            username='seleniumuser',
            email='selenium@example.com',
            pw_hash=generate_password_hash('password'),
            display_name='Selenium User'
        )
        db.session.add(self.user)
        db.session.commit()

        # Start the Flask server in a thread
        self.server = ServerThread(self.app)
        self.server.start()
        time.sleep(1)  # Give the server time to start

        # Setup Selenium WebDriver
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

    def tearDown(self):
        self.driver.quit()
        self.server.shutdown()

        # Clean up DB after test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        self.driver.get('http://localhost:5000/login')
        self.driver.find_element(By.NAME, 'email').send_keys('selenium@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('password')
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

    # ... your test methods as before ...


    def test_home_page(self):
        self.driver.get('http://localhost:5000/')
        self.assertIn('Podfolio', self.driver.title)

    def test_signup(self):
        self.driver.get('http://localhost:5000/signup')
        self.driver.find_element(By.NAME, 'name').send_keys('New User')
        self.driver.find_element(By.NAME, 'email').send_keys('newuser@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('Test123!')
        self.driver.find_element(By.NAME, 'confirm_password').send_keys('Test123!')
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

    def test_login(self):
        self.login()

    def test_navigation(self):
        self.driver.get('http://localhost:5000/')
        self.driver.find_element(By.LINK_TEXT, 'Login').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))
        self.driver.find_element(By.LINK_TEXT, 'Sign up').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/signup'))

    def test_friend_page_access(self):
        self.driver.get('http://localhost:5000/friends')
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))

    def test_logout(self):
        self.login()
        self.driver.find_element(By.LINK_TEXT, 'Logout').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/'))

    def test_log_podcast_with_existing_db_entry(self):
        self.login()

        podcast = Podcast(
            spotify_id='test123',
            name='Test Podcast',
            description='Testing'
        )
        db.session.add(podcast)
        db.session.commit()

        # Simulate logging podcast via JS fetch (POST)
        self.driver.execute_script("""
            fetch('/log_podcast', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    podcast_id: 'test123',
                    episode: 'Test Episode',
                    platform: 'Spotify',
                    duration: 30,
                    rating: 4.5,
                    genre: 'Tech'
                })
            }).then(r => r.json()).then(console.log);
        """)

        # Give it some time to process
        time.sleep(2)

        # Check that log exists
        from app.models import PodcastLog
        logs = PodcastLog.query.filter_by(user_id=self.user.id).all()
        self.assertGreaterEqual(len(logs), 1)

    def test_autocomplete_podcast_search(self):
        podcast = Podcast(name="Learning Python", spotify_id="p1", description="desc")
        db.session.add(podcast)
        db.session.commit()

        self.login()

        self.driver.get("http://localhost:5000/podcast-log")
        self.driver.execute_script("""
            fetch('/search_podcast_names?q=Learning')
              .then(r => r.json())
              .then(data => console.log(data));
        """)
        time.sleep(2)  # Allow JS to run


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(SeleniumTestCase)
