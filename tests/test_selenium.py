import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException,TimeoutException,StaleElementReferenceException
from selenium.webdriver.common.alert import Alert
import time
import random
import string


class SeleniumTestCase(unittest.TestCase):
    def setUp(self):
        # Setup Selenium WebDriver
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.base_url = "http://127.0.0.1:5000"
        
        # Generate random test user credentials
        username = 'testuser_' + ''.join(random.choices(string.ascii_lowercase, k=5))
        self.test_user = {
            'username': username,
            'email': f'{username}@example.com',  # Match email prefix to username
            'password': 'Test@1234',
            'display_name': 'Test User'
        }


    def tearDown(self):
        self.driver.quit()

    def signup(self):
        self.driver.get(f'{self.base_url}/signup')
        self.driver.find_element(By.NAME, 'name').send_keys(self.test_user['username'])
        self.driver.find_element(By.NAME, 'email').send_keys(self.test_user['email'])
        self.driver.find_element(By.NAME, 'password').send_keys(self.test_user['password'])
        self.driver.find_element(By.NAME, 'confirm_password').send_keys(self.test_user['password'])
        submit_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(0.5)
        submit_button.click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

    def login(self):
        self.driver.get(f'{self.base_url}/login')
        self.driver.find_element(By.NAME, 'email').send_keys(self.test_user['email'])
        self.driver.find_element(By.NAME, 'password').send_keys(self.test_user['password'])
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))

    def logout(self):
        self.driver.find_element(By.LINK_TEXT, 'Log Out').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/'))

    # Tests

    def test_home_page(self):
        self.driver.get(self.base_url)
        self.assertIn('Podfolio', self.driver.title)

    def test_signup_and_login(self):
        # Test signup
        self.signup()
        
        # Verify we're on the podcast log page after signup
        self.assertIn('/podcast-log', self.driver.current_url)
        
        # Logout
        self.logout()
        
        # Test login with same credentials
        self.login()
        
        # Verify we're logged in
        self.assertIn('/podcast-log', self.driver.current_url)

    def test_navigation(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element(By.LINK_TEXT, 'Get Started')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # allow layout to stabilize
        element.click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/signup'))
        self.driver.find_element(By.LINK_TEXT, 'Sign Up').click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/signup'))

    def test_friend_page_access(self):
        self.driver.get(f'{self.base_url}/friends')
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))

    def test_logout(self):
        self.signup()
        self.logout()
        self.assertIn(self.base_url, self.driver.current_url)

    def test_duplicate_signup(self):
        # First signup should work
        self.signup()
        self.logout()
        
        # Second signup with same email should fail
        self.driver.get(f'{self.base_url}/signup')
        self.driver.find_element(By.NAME, 'name').send_keys(self.test_user['username'])
        self.driver.find_element(By.NAME, 'email').send_keys(self.test_user['email'])
        self.driver.find_element(By.NAME, 'password').send_keys(self.test_user['password'])
        self.driver.find_element(By.NAME, 'confirm_password').send_keys(self.test_user['password'])
        submit_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(0.5)
        submit_button.click()
        
        # Wait for response and check for error message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.alert-warning'))
        )
        error_messages = self.driver.find_elements(By.CSS_SELECTOR, '.alert-warning')

        
        # Check if any error message contains text about duplicate email
        duplicate_email_found = any(
            'email' in message.text.lower() and 'already' in message.text.lower()
            for message in error_messages
        )
        self.assertTrue(duplicate_email_found, "Expected duplicate email error message not found")

    def test_log_podcast_from_ui(self):
        self.signup()
        
        self.driver.get(f'{self.base_url}/podcast-log')

        podcast_input = self.driver.find_element(By.ID, "podcastName")
        podcast_input.clear()
        podcast_input.send_keys("test")

        # Wait for podcast suggestions dropdown and at least one item
        pod_suggestions = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "podcastSuggestions"))
        )
        first_podcast = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#podcastSuggestions .autocomplete-item"))
        )

        # Select the first podcast suggestion
        first_podcast.click()

        # Wait for episodes to be fetched and episode input enabled
        episode_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'podcastEp'))
        )
        time.sleep(5)
        # Now type episode name to trigger episode suggestions
        episode_input.send_keys('#1')

        # Wait for episode suggestions dropdown to appear
        episode_suggestion = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#episodeSuggestions .autocomplete-item'))
        )
        episode_suggestion.click()
        selected_episode_value = episode_input.get_attribute('value')
        
        # Select platform
        Select(self.driver.find_element(By.ID, 'platform')).select_by_visible_text('Spotify')

        # Fill duration
        listen_time = self.driver.find_element(By.ID, 'listenTime')
        listen_time.clear()
        listen_time.send_keys('45')

        # Select genre
        Select(self.driver.find_element(By.ID, 'genre')).select_by_visible_text('Educational')

        # Select 5-star rating
        star_label = self.driver.find_element(By.CSS_SELECTOR, "label[for='star5']")
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", star_label)
        time.sleep(0.5)
        star_label.click()

        # Fill review (optional)
        review_input = self.driver.find_element(By.ID, 'review')
        review_input.clear()
        review_input.send_keys('Great episode!')

        # Submit form
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button.btn-log')
        submit_button.click()

        # Wait for alert and verify
        try:
            WebDriverWait(self.driver, 10).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            self.assertEqual(alert.text, "Podcast logged successfully!")
            alert.accept()
        except NoAlertPresentException:
            # Check if success message is shown on page instead
            self.assertIn("Podcast logged successfully!", self.driver.page_source)

    def test_unauthenticated_podcast_log_access(self):
        self.driver.get(f'{self.base_url}/logout')
        self.driver.get(f'{self.base_url}/podcast-log')
        WebDriverWait(self.driver, 10).until(EC.url_contains('/login'))



    def test_update_profile_display_name(self):
        self.signup()
        self.driver.get(f'{self.base_url}/settings')

        # Generate new display name
        new_display_name = 'Updated Display Name ' + ''.join(random.choices(string.ascii_letters, k=5))

        # Find and update display name field
        display_name_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'display_name'))
        )
        display_name_input.clear()
        display_name_input.send_keys(new_display_name)

        # Find save button and scroll it into view
        save_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[text()="Save Settings"]'))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
        time.sleep(0.5)  # Allow scroll to complete

        # Wait for button to be clickable and click it
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Save Settings"]'))
        ).click()

        # Wait for update to complete and verify using EC.text_to_be_present_in_element_value
        locator = (By.NAME, 'display_name')
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element_value(locator, new_display_name)
        )

    def test_send_and_accept_friend_request(self):
        # Create first test user (main user)
        self.signup()
        
        # Get the actual username that was registered
        main_username = self.test_user['username']
        
        # Logout the first user
        self.logout()
        
        # Create second test user credentials
        username = 'frienduser_' + ''.join(random.choices(string.ascii_lowercase, k=5))
        friend_user = {
            'username': username,
            'email': f'{username}@example.com',
            'password': 'Friend@1234',
            'display_name': 'Friend User'
        }

        # Sign up second user
        self.driver.get(f'{self.base_url}/signup')
        self.driver.find_element(By.NAME, 'name').send_keys(friend_user['username'])
        self.driver.find_element(By.NAME, 'email').send_keys(friend_user['email'])
        self.driver.find_element(By.NAME, 'password').send_keys(friend_user['password'])
        self.driver.find_element(By.NAME, 'confirm_password').send_keys(friend_user['password'])
        submit_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(0.5)
        submit_button.click()
        WebDriverWait(self.driver, 10).until(EC.url_contains('/podcast-log'))
        
        # Second user sends friend request to first user
        self.driver.get(f'{self.base_url}/friends')
        
        # Wait for the search input by ID
        search_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'friendSearch'))
        )
        search_input.send_keys(main_username)
        
        # Click the send request button
        send_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'sendRequestBtn'))
        )
        send_btn.click()
        
        # Handle any alerts that might appear
        try:
            alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
            alert.accept()
        except (NoAlertPresentException, TimeoutException):
            pass
        
        # Logout second user
        self.logout()
        
        # First user logs in to accept request
        self.login()
        self.driver.get(f'{self.base_url}/friends')
        
        # Accept the friend request
        try:
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.accept-btn'))
            )
            accept_button.click()
            time.sleep(1)
        except TimeoutException:
            pass
        time.sleep(4)
        # Verify the friend appears in the friends list
        page_source = self.driver.page_source
        self.assertIn(friend_user['username'], page_source)


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(SeleniumTestCase)


if __name__ == '__main__':
    unittest.main(verbosity=2)