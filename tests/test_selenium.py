import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.models import User, Podcast,PodcastLog
import threading
import time
from werkzeug.serving import make_server
import tempfile
import os
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from selenium.webdriver.common.alert import Alert



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
        # Set environment variables for Spotify credentials
        os.environ['SPOTIFY_CLIENT_ID'] = "41f896f36304442fbb01a77a11c0aebb"
        os.environ['SPOTIFY_CLIENT_SECRET'] = "99c407e2cbe048e684b172c76c92896a"
        # Create temp file for SQLite db that is accessible across threads
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='.sqlite')
    
    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        os.unlink(cls.db_path)  # Remove temp db file
    
    def setUp(self):
        self.app = create_app()
        self.app.config.update({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
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
            display_name='Selenium User'
        )
        self.user.set_password('ewuf@132')
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
        self.driver.find_element(By.NAME, 'password').send_keys('ewuf@132')
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

    # Tests


    def test_home_page(self):
        self.driver.get('http://localhost:5000/')
        self.assertIn('Podfolio', self.driver.title)

    def test_signup(self):
        self.driver.get('http://localhost:5000/signup')
        self.driver.find_element(By.NAME, 'name').send_keys('New User')
        self.driver.find_element(By.NAME, 'email').send_keys('newuser@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('Test123!')
        self.driver.find_element(By.NAME, 'confirm_password').send_keys('Test123!')
        submit_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        submit_button.click()

        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

    def test_login(self):
        self.login()

    def test_navigation(self):
        self.driver.get('http://localhost:5000/')
        element = self.driver.find_element(By.LINK_TEXT, 'Get Started')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # allow layout to stabilize
        element.click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))
        self.driver.find_element(By.LINK_TEXT, 'Sign Up').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/signup'))

    def test_friend_page_access(self):
        self.driver.get('http://localhost:5000/friends')
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))

    def test_logout(self):
        self.login()
        self.driver.find_element(By.LINK_TEXT, 'Log Out').click()
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

    def test_send_and_accept_friend_request(self):
        # Create user B
        user_b = User(username='frienduser', email='friend@example.com', display_name='Friend User')
        user_b.set_password('pafdn@123')
        db.session.add(user_b)
        db.session.commit()

        # User A logs in and sends request
        self.login()  # seleniumuser
        self.driver.get('http://localhost:5000/friends')
        # Wait for the search input by ID
        search_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'friendSearch'))
        )
        search_input.send_keys('frienduser')
        
        # Click the send request button
        send_btn = self.driver.find_element(By.ID, 'sendRequestBtn')
        send_btn.click()
        time.sleep(1)

        self.driver.find_element(By.LINK_TEXT, 'Log Out').click()

        # User B logs in and accepts
        self.driver.get('http://localhost:5000/login')
        self.driver.find_element(By.NAME, 'email').send_keys('friend@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('pafdn@123')
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

        # Accept the friend request
        self.driver.get('http://localhost:5000/friends')
        accept_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'accept-btn'))
        )
        accept_button.click()
        time.sleep(1)

        # Assert the friend request is now a friend
        page_source = self.driver.page_source
        self.assertIn('seleniumuser', page_source)

    def test_log_podcast_from_ui(self):
        self.login()



        self.driver.get('http://localhost:5000/podcast-log')

        # Type podcast name (simulate user input)
        podcast_input = self.driver.find_element(By.ID, "podcastName")
        podcast_input.clear()
        podcast_input.send_keys("joe")

        # Wait for suggestions to load
        suggestions = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "podcastSuggestions"))
        )

        # Wait for at least one suggestion item to appear
        first_suggestion = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#podcastSuggestions .autocomplete-item"))
        )

        # Click the first suggestion to select the podcast
        first_suggestion.click()

        # Fill in the rest of the form by ID
        self.driver.find_element(By.ID, 'podcastEp').send_keys('Episode 1')
        Select(self.driver.find_element(By.ID, 'platform')).select_by_visible_text('Spotify')
        self.driver.find_element(By.ID, 'listenTime').send_keys('45')
        Select(self.driver.find_element(By.ID, 'genre')).select_by_visible_text('Educational')

        # Select 5-star rating
        # Find the label associated with #star5
        star_label = self.driver.find_element(By.CSS_SELECTOR, "label[for='star5']")

        # Scroll it into view
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", star_label)

        # Click it
        star_label.click()

        # Submit the form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn-log')
        submit_button.click()
 
        try:
            WebDriverWait(self.driver, 10).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            self.assertEqual(alert.text, "Podcast logged successfully!")
            alert.accept()
        except NoAlertPresentException:
            self.fail("Expected alert did not appear.")

        logs = PodcastLog.query.filter_by(user_id=self.user.id).all()
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[-1].ep_name, 'Episode 1')


    def test_unauthenticated_podcast_log_access(self):
        self.driver.get('http://localhost:5000/logout')
        self.driver.get('http://localhost:5000/podcast-log')
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))

    def test_update_profile_display_name(self):
        self.login()
        self.driver.get('http://localhost:5000/settings')

        display_name_input = self.driver.find_element(By.NAME, 'display_name')
        display_name_input.clear()
        display_name_input.send_keys('New Display Name')

        save_button = self.driver.find_element(By.XPATH, '//button[text()="Save Settings"]')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
        save_button.click()

        time.sleep(1)  # wait for the update to complete

        # Re-query the user fresh from the DB to avoid session issues
        updated_user = db.session.query(User).filter_by(id=self.user.id).first()
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.display_name, 'New Display Name')



def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(SeleniumTestCase)
