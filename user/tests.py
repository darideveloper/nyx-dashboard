from time import sleep

from django.core import mail
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import LiveServerTestCase

from utils.automation import get_selenium_elems
from utils.tokens import get_id_token, validate_user_token

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
        
        
class LogInTest(LiveServerTestCase):
    """ Validate user login with selenium """

    def setUp(self):
        
        # Create a user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
        )
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Load login page
        self.login_url = self.live_server_url + "/admin/login/"
        self.driver.get(self.login_url)
        
        # Fiend fields
        selectors = {
            "username": "input[name='username']",
            "password": "input[name='password']",
            "submit": "button[type='submit']",
        }
        self.fields = get_selenium_elems(self.driver, selectors)
                
        self.error_message = "Invalid email or password"
        
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass
        
    def test_redirect(self):
        """ Redirect to sign up page """
        
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/login/?next=/landing")
    
    def test_valid(self):
        """ Test login with valid email and password.
        Expecting valid """
                
        # Submit form
        self.fields["username"].send_keys(self.auth_username)
        self.fields["password"].send_keys(self.password)
        self.fields["submit"].click()
        
        # Validate redirect
        self.assertNotEqual(self.driver.current_url, self.login_url)
        
    def test_already_logged(self):
        """ Test login when its already logged. """
        
        # Login
        self.client.force_login(self.auth_user)
        
        # Load login page
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
                
    def test_invalid_email(self):
        """ Test login with invalid email.
        Expecting login failure """
                
        # Submit form
        self.fields["username"].send_keys("invalid email")
        self.fields["password"].send_keys(self.password)
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        self.assertEqual(error_message, self.error_message)
    
    def test_invalid_password(self):
        """ Test login with invalid password.
        Expecting login failure"""
                
        # Submit form
        self.fields["username"].send_keys(self.auth_username)
        self.fields["password"].send_keys("invalid password")
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        self.assertEqual(error_message, self.error_message)
        
    def test_no_staff(self):
        """ Test login no staff user.
        Expecting login failure"""
                
        self.auth_user.is_staff = False
        self.auth_user.save()
        
        # Submit form
        self.fields["username"].send_keys(self.auth_username)
        self.fields["password"].send_keys(self.password)
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        self.assertEqual(error_message, self.error_message)


class SignUpTest(LiveServerTestCase):
    """ Validate register user with selenium """
    
    def setUp(self):
        
        # Create a user
        self.old_auth_username = "old_test_user@gmail.com"
        self.old_password = "old_test_password"
        self.auth_user = User.objects.create_user(
            username=self.old_auth_username,
            email=self.old_auth_username,
            password=self.old_password,
            first_name="first",
            last_name="last",
            is_staff=True,
            is_active=True,
        )
        
        # Create "buyers" group
        self.buyers_group = Group.objects.create(name='buyers')
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Load login page
        self.sign_up_url = self.live_server_url + "/user/sign-up/"
        self.driver.get(self.sign_up_url)
        
        # Initial fields and data
        selectors = {
            "email": "input[name='email']",
            "password1": "input[name='password1']",
            "password2": "input[name='password2']",
            "first_name": "input[name='first-name']",
            "last_name": "input[name='last-name']",
            "submit": "button[type='submit']",
        }
        
        self.fields = get_selenium_elems(self.driver, selectors)
        
        self.data = {
            "email": "test@gmail.com",
            "password_valid": "Test_pass1**",
            "password_invalid": "test_pass",
            "first_name": "Test",
            "last_name": "User",
        }
        
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass

    def test_redirect(self):
        """ Redirect to sign up page """
        
        response = self.client.get("/sign-up/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/user/sign-up/")
    
    def test_valid(self):
        """ Try to register new user with valid data """
                
        # Submit form
        self.fields["email"].send_keys(self.data["email"])
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
                        
        # Validate user created
        user = User.objects.get(username=self.data["email"])
        self.assertEqual(user.first_name, self.data["first_name"])
        self.assertEqual(user.last_name, self.data["last_name"])
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_active)
        
        # Vlidate redirect user group
        user_in_group = self.buyers_group.user_set.filter(username=user).exists()
        self.assertTrue(user_in_group)
        
        # Validate sweet alert confirmation
        sweet_alert_data = {
            ".swal2-title": "Done",
            ".swal2-title + div": "User created successfully. "
                                  "Check your email to confirm your account."
        }
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
         
        # validate activation email sent
        self.assertEqual(len(mail.outbox), 1)
          
        # Validate email text content
        subject = "Activate your Nyx Trackers account"
        cta_link_base = f"{settings.HOST}/user/activate/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        self.assertIn(user.first_name, sent_email.body)
        self.assertIn(user.last_name, sent_email.body)
        
        # Validate email html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        
        # Validate token
        token_elems = sent_email.body.split(cta_link_base)[1].split("/")[0]
        _, token_1, token_2 = token_elems.split("-")
        token = f"{token_1}-{token_2}"
        token_valid = validate_user_token(user.id, token)
        self.assertTrue(token_valid)
        
    def test_already_logged(self):
        """ Test sign up with valid email and password """
        
        # Login
        self.client.force_login(self.auth_user)
        
        # Load login page
        response = self.client.get("/user/sign-up/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
    
    def test_already_used_email(self):
        """ Try to register with already used email."""
                
        # Submit form
        self.fields["email"].send_keys(self.old_auth_username)
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
                        
        # Validate user not created
        user = User.objects.filter(username=self.data["email"])
        self.assertFalse(user.exists())
        
        # Validate sweet alert error
        sweet_alert_data = {
            ".swal2-title": "Error",
            ".swal2-title + div": "Email already used. "
                                  "Try to login instead. "
                                  "If you just created an account, "
                                  "check your email to activate it.",
        }
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
            
    def test_valid_guest(self):
        """ Try to register with already used email (but is guest user) """
        
        # Delete first name and last name and deactivate user
        self.auth_user.first_name = ""
        self.auth_user.last_name = ""
        self.auth_user.is_active = False
        self.auth_user.save()
        
        # Submit form
        self.fields["email"].send_keys(self.old_auth_username)
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
        
        # Regular sign up validation
        
        # Vlidate redirect user group
        user_in_group = self.buyers_group.user_set.filter(
            username=self.auth_user
        ).exists()
        self.assertTrue(user_in_group)
        
        # Validate sweet alert confirmation
        sweet_alert_data = {
            ".swal2-title": "Done",
            ".swal2-title + div": "User created successfully. "
                                  "Check your email to confirm your account."
        }
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
         
        # validate activation email sent
        self.assertEqual(len(mail.outbox), 1)
          
        # Validate email text content
        subject = "Activate your Nyx Trackers account"
        cta_link_base = f"{settings.HOST}/user/activate/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        self.assertIn(self.auth_user.first_name, sent_email.body)
        self.assertIn(self.auth_user.last_name, sent_email.body)
        
        # Validate email html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        
        # Validate token
        token_elems = sent_email.body.split(cta_link_base)[1].split("/")[0]
        _, token_1, token_2 = token_elems.split("-")
        token = f"{token_1}-{token_2}"
        is_valid = validate_user_token(self.auth_user.id, token)
        self.assertTrue(is_valid)
        
    def test_already_used_email_no_active(self):
        """ Try to register with already used email (but not active) """
        
        # Update user
        self.auth_user.is_active = False
        self.auth_user.save()
                
        # Submit form
        self.fields["email"].send_keys(self.old_auth_username)
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
                        
        # Validate user not created
        user = User.objects.filter(username=self.data["email"])
        self.assertFalse(user.exists())
        
        # Validate sweet alert error
        sweet_alert_data = {
            ".swal2-title": "Done",
            ".swal2-title + div": "Account already created. "
                                  "Check your email to confirm your account."
        }
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
    
    def test_password_mismatch(self):
        """ Try to register with mismatched passwords."""
                
        # Submit form
        self.fields["email"].send_keys(self.data["email"])
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"] + "extra text")
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        self.assertEqual(error_message, "Passwords do not match")
    
    def test_password_invalid(self):
        """ Try to register with invalid password."""
                
        # Submit form
        self.fields["email"].send_keys(self.data["email"])
        self.fields["password1"].send_keys(self.data["password_invalid"])
        self.fields["password2"].send_keys(self.data["password_invalid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        error_message = "Password must be 8-50 characters long and contain " \
            "at least one lowercase letter one uppercase letter and one number"
        self.assertEqual(error_message, error_message)
        
    def test_email_invalid(self):
        """ Try to register with invalid email."""
                
        # Submit form
        self.fields["email"].send_keys("invalid email")
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
        
        # Validate fotm no sent / user no created
        user = User.objects.filter(username="invalid email")
        self.assertFalse(user.exists())
        
        
class AdminTest(LiveServerTestCase):
    """ Validate admins custom functions """
    
    def setUp(self):
        
        # Create a user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
            first_name="first",
            last_name="last",
            email="test@mail.com",
        )
        
        # Create "buyers" group
        self.buyers_group = Group.objects.create(name='buyers')
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass
        
    def __login__(self):
        """ Login with valid user and password """
        
        # Load home page
        home_page = self.live_server_url + "/login/"
        self.driver.get(home_page)
        
        # Login
        selectors = {
            "username": "input[name='username']",
            "password": "input[name='password']",
            "submit": "button[type='submit']",
        }
        fields = get_selenium_elems(self.driver, selectors)
        fields["username"].send_keys(self.auth_username)
        fields["password"].send_keys(self.password)
        fields["submit"].click()
        
        # go to admin
        admin_page = self.live_server_url + "/admin/"
        self.driver.get(admin_page)
        
    def test_redirect_accounts_profile(self):
        """ Test redirect to admin page """
        
        response = self.client.get("/accounts/profile/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
        
    def test_cookie_logged(self):
        """ Test cookie saved after login """
        
        # Validate login cookie saved
        user_full_name = f"{self.auth_user.first_name} {self.auth_user.last_name}"
        
        # Login
        self.__login__()
        
        # Go to admin
        admin_page = self.live_server_url + "/admin/"
        self.driver.get(admin_page)
        
        # Validate "nyx" cookie
        cookie_username = self.driver.get_cookie("nyx_username")
        cookie_email = self.driver.get_cookie("nyx_email")
        self.assertIn(user_full_name, cookie_username["value"])
        self.assertIn(self.auth_user.email, cookie_email["value"])
        
    def test_cookie_logout(self):
        """ Test cookie deleted after logout """
        
        # Close session
        logout_page = self.live_server_url + "/admin/logout/"
        self.driver.get(logout_page)
        
        # Validate no cookie
        cookies = self.driver.get_cookies()
        cookie = [cookie for cookie in cookies if cookie["name"] == "nyx"]
        self.assertEqual(cookie, [])

    def test_landing_top_bar_link(self):
        """ Validate landing button in top bar """
        
        # Data and selectors
        links = {
            "home": {
                "text": "Home",
                "selector": ".d-sm-inline-block a.nav-link",
                "value": settings.LANDING_HOST + "/"
            }
        }
        
        links_selectors = {}
        for link_key, link_data in links.items():
            links_selectors[link_key] = link_data["selector"]
        
        # Login
        self.__login__()
        
        # Get links
        links_elems = get_selenium_elems(self.driver, links_selectors)
        for link_key, link_data in links.items():
            link_elem = links_elems[link_key]
            
            # Validate data
            self.assertEqual(link_elem.get_attribute("href"), link_data["value"])
            self.assertEqual(link_elem.text, link_data["text"])
        

class ActivationTest(LiveServerTestCase):
    """ Activate user account with email token """
    
    def setUp(self):
        
        # Create a user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
        )
        
        # Create "buyers" group
        self.buyers_group = Group.objects.create(name='buyers')
        self.urls = {
            "sign-up": "/user/sign-up/",
        }
        
        # Register a user
        self.form_data = {
            "email": "test@gmail.com",
            "password1": "Test_pass1**",
            "password2": "Test_pass1**",
            "first-name": "Test",
            "last-name": "User",
        }
        self.client.post(self.urls["sign-up"], self.form_data)
        
        self.user = User.objects.get(username=self.form_data["email"])
        
        # validate activation email sent
        self.assertEqual(len(mail.outbox), 1)
          
        # Validate token
        sent_email = mail.outbox[0]
        self.cta_link_base = f"{settings.HOST}/user/activate/"
        token_elems = sent_email.body.split(self.cta_link_base)[1].split("/")[0]
        self.user_id, token_1, token_2 = token_elems.split("-")
        self.token = f"{token_1}-{token_2}"
        
        # Alert data
        self.sweet_alert_data_error = {
            ".swal2-title": "Activation Error",
            ".swal2-title + div": "Check the link or try to sign up again."
        }
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
                
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass
        
    def __get_activation_link__(self, user_id, token):
        """ Get token link """
        link = f"{self.live_server_url}/user/activate/{user_id}-{token}/"
        return link
        
    def __validate_sweet_alert__(self, sweet_alert_data):
        """ Validate sweet alert """
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
    
    def __click_sweet_alert__(self):
        """ Click on sweet alert confirmation """
        
        # Click on login button
        login_button = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
        login_button.click()
        sleep(1)
    
    def test_valid_token(self):
        """ Try to activate user account with email token """
                
        # Load activation link
        activation_link = self.__get_activation_link__(self.user_id, self.token)
        self.driver.get(activation_link)
                
        # Check if user is active
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        
        # Validate alert
        self.__validate_sweet_alert__({
            ".swal2-title": "Account Activated",
            ".swal2-title + div": "Your account has been activated successfully. "
                                  "Now you can login."
        })
        
        # Click on login button
        self.__click_sweet_alert__()
        
        # Validate redirect to landing
        self.assertEqual(self.driver.current_url, settings.LANDING_HOST + "/")
    
    def test_valid_token_guest(self):
        """ Try to activate user account with email token
        for a guest user """
                
        # Load activation link
        activation_link = self.__get_activation_link__(self.user_id, self.token)
        self.driver.get(activation_link)
                
        # Check if user is active
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        
        # Validate alert
        self.__validate_sweet_alert__({
            ".swal2-title": "Account Activated",
            ".swal2-title + div": "Your account has been activated successfully. "
                                  "Now you can login."
        })
        
        # Click on login button
        self.__click_sweet_alert__()
        
        # Validate redirect to landing
        self.assertEqual(self.driver.current_url, settings.LANDING_HOST + "/")
    
    def test_already_logged(self):
        """ Test activation with valid email and password."""
        
        # Login
        self.client.force_login(self.auth_user)
        
        # Load login page
        response = self.client.get("/user/activate/1-1/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
    
    def test_invalid_token(self):
        """ Try to activate user account with invalid email token """
                
        # Load activation link
        activation_link = self.__get_activation_link__(self.user_id, "invalid_token")
        self.driver.get(activation_link)
        
        # Check if user keeps inactive
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        
        # Validate error message
        self.__validate_sweet_alert__(self.sweet_alert_data_error)
            
    def test_invalid_user(self):
        """ Try to activate user account with invalid user id """
                
        # Load activation link
        activation_link = self.__get_activation_link__("99", self.token)
        self.driver.get(activation_link)
        
        # Check if user keeps inactive
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        
        # Validate error message
        self.__validate_sweet_alert__(self.sweet_alert_data_error)
        
        
class ForgottenPassTest(LiveServerTestCase):
    """ Test forgotten password view """
    
    def setUp(self):
        
        # Create a user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
            first_name="first",
            last_name="last"
        )
        
        # Create "buyers" group
        self.buyers_group = Group.objects.create(name='buyers')
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass
    
    def test_already_logged(self):
        """ Test activation when its already logged. """
        
        # Login
        self.client.force_login(self.auth_user)
        
        # Load login page
        response = self.client.get("/user/forgotten-pass/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
    
    def test_send_form(self):
        """ Test send form and validate password reset email """
        
        # Load forgotten password page
        forgotten_pass_url = self.live_server_url + "/user/forgotten-pass/"
        self.driver.get(forgotten_pass_url)
        
        # Fiend fields
        selectors = {
            "email": "input[name='email']",
            "submit": "button[type='submit']",
        }
        fields = get_selenium_elems(self.driver, selectors)
        
        # Submit form
        fields["email"].send_keys(self.auth_username)
        fields["submit"].click()
        
        # Validate email sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Validate email text content
        subject = "Reset your Nyx Trackers password"
        cta_link_base = f"{settings.HOST}/user/reset-pass/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        self.assertIn(self.auth_user.first_name, sent_email.body)
        self.assertIn(self.auth_user.last_name, sent_email.body)
        
        # Validate email html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        
        # Validate token
        token_elems = sent_email.body.split(cta_link_base)[1].split("/")[0]
        _, token_1, token_2 = token_elems.split("-")
        token = f"{token_1}-{token_2}"
        token_manager = PasswordResetTokenGenerator()
        token_valid = token_manager.check_token(self.auth_user, token)
        self.assertTrue(token_valid)
        
        # Validate sweet alert confirmation
        sweet_alert_data = {
            ".swal2-title": "Email sent",
            ".swal2-title + div": "If your email is registered, "
                                  "you will receive an email with instructions "
                                  "to reset your password.",
        }
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
            
    def test_send_form_invalid_email(self):
        """ Test send form with invalid email """
        
        # Load forgotten password page
        forgotten_pass_url = self.live_server_url + "/user/forgotten-pass/"
        self.driver.get(forgotten_pass_url)
        
        # Fiend fields
        selectors = {
            "email": "input[name='email']",
            "submit": "button[type='submit']",
        }
        fields = get_selenium_elems(self.driver, selectors)
        
        # Submit form
        fields["email"].send_keys("no-user@gmail.com")
        fields["submit"].click()
        
        # Validate no email sent
        self.assertEqual(len(mail.outbox), 0)
        
        # Validate sweet alert confirmation
        sweet_alert_data = {
            ".swal2-title": "Email sent",
            ".swal2-title + div": "If your email is registered, "
                                  "you will receive an email with instructions "
                                  "to reset your password.",
        }
        
        for selector, text in sweet_alert_data.items():
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.assertEqual(elem.text, text)
            
            
class ResetPassTest(LiveServerTestCase):
    """ Activate user account with email token """
    
    def setUp(self):
        
        # Create a user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
            is_active=True,
        )
        self.user_id = self.auth_user.id
        
        self.id_token = get_id_token(self.auth_user)
        self.token = "-".join(self.id_token.split("-")[1:])
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Error message
        self.sweet_alert_data_error = {
            "title": "Reset Password Error",
            "body": "Check the link or try to reset your password again.",
        }
        
        # Passwords
        self.password_valid = "Test_pass1**"
        self.password_invalid = "test_pass"
        
        # Form inputs
        self.form_selectors = {
            "password1": "input[name='new-password-1']",
            "password2": "input[name='new-password-2']",
            "submit": "button[type='submit']",
        }
                
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass
        
    def __get_reset_link__(self, user_id, token):
        """ Get token link """
        link = f"{self.live_server_url}/user/reset-pass/{user_id}-{token}/"
        return link
        
    def __validate_sweet_alert__(self, title: str, body: str):
        """ Validate sweet alert """
        
        selectors = {
            "title": ".swal2-title",
            "body": ".swal2-title + div",
        }
        
        title_elem = self.driver.find_element(By.CSS_SELECTOR, selectors["title"])
        body_elem = self.driver.find_element(By.CSS_SELECTOR, selectors["body"])
        self.assertEqual(title_elem.text, title)
        self.assertEqual(body_elem.text, body)
        
    def test_already_logged(self):
        """ Test reset pass when its already logged. """
        
        # Login
        self.client.force_login(self.auth_user)
        
        # Load login page
        response = self.client.get("/user/activate/1-1/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
        
    def test_get_valid_id_token(self):
        """ Try toload reset pass form with valid email token """
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, self.token)
        self.driver.get(activation_link)
        
        # Validate no alert
        alert_elems = self.driver.find_elements(By.CSS_SELECTOR, ".swal2-title")
        self.assertEqual(alert_elems, [])
    
    def test_get_invalid_token(self):
        """ Try to reset password with invalid email token """
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, "invalid_token")
        self.driver.get(activation_link)
        
        # Validate error message
        self.__validate_sweet_alert__(**self.sweet_alert_data_error)
            
    def test_get_invalid_user(self):
        """ Try to reset password with invalid user id """
                
        # Load activation link
        activation_link = self.__get_reset_link__("99", self.token)
        self.driver.get(activation_link)
        
        # Validate error message
        self.__validate_sweet_alert__(**self.sweet_alert_data_error)
    
    def test_post_invalid_token(self):
        """ Try to reset password with invalid email token """
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, self.token)
        self.driver.get(activation_link)
        
        # Update form action
        activation_link = self.__get_reset_link__(self.user_id, "invalid_token")
        code = f"document.querySelector('form').action = '{activation_link}';"
        self.driver.execute_script(code)
        
        # Submit post data
        fields = get_selenium_elems(self.driver, self.form_selectors)
        fields["password1"].send_keys(self.password_valid)
        fields["password2"].send_keys(self.password_valid)
        fields["submit"].click()
                
        # Validate error message
        self.__validate_sweet_alert__(**self.sweet_alert_data_error)
        
    def test_post_invalid_user(self):
        """ Try to reset password with invalid user id """
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, self.token)
        self.driver.get(activation_link)
        
        # Update form action with js
        activation_link = self.__get_reset_link__("99", self.token)
        code = f"document.querySelector('form').action = '{activation_link}';"
        self.driver.execute_script(code)
                
        # Submit post data
        fields = get_selenium_elems(self.driver, self.form_selectors)
        fields["password1"].send_keys(self.password_valid)
        fields["password2"].send_keys(self.password_valid)
        fields["submit"].click()
        
        # Validate error message
        self.__validate_sweet_alert__(**self.sweet_alert_data_error)
        
    def test_post_valid(self):
        """ Try to reset password with valid user id and token"""
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, self.token)
        self.driver.get(activation_link)
        
        # Submit post data
        fields = get_selenium_elems(self.driver, self.form_selectors)
        fields["password1"].send_keys(self.password_valid)
        fields["password2"].send_keys(self.password_valid)
        fields["submit"].click()
        
        # Validate error message
        self.__validate_sweet_alert__(
            title="Password Updated",
            body="Your password has been updated successfully. "
                 "Now you can login."
        )
        
    def test_invalid_password(self):
        """ Try to reset password with invalid password """
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, self.token)
        self.driver.get(activation_link)
        
        # Submit post data
        fields = get_selenium_elems(self.driver, self.form_selectors)
        fields["password1"].send_keys(self.password_invalid)
        fields["password2"].send_keys(self.password_invalid)
        fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        error_message = "Password must be 8-50 characters long and contain " \
            "at least one lowercase letter one uppercase letter and one number"
        self.assertEqual(error_message, error_message)
        
    def test_missmatch_password(self):
        """ Try to reset password with mismatched passwords """
                
        # Load activation link
        activation_link = self.__get_reset_link__(self.user_id, self.token)
        self.driver.get(activation_link)
        
        # Submit post data
        fields = get_selenium_elems(self.driver, self.form_selectors)
        fields["password1"].send_keys(self.password_valid)
        fields["password2"].send_keys(self.password_valid + "extra text")
        fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        self.assertEqual(error_message, "Passwords do not match")