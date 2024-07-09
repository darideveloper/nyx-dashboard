from django.test import LiveServerTestCase
from django.test import Client
from django.contrib.auth.models import User, Group
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from user import tools

        
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
        chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Load login page
        self.login_url = self.live_server_url + "/admin/login/"
        self.driver.get(self.login_url)
        
        # Fiend fields
        selectos = {
            "username": "input[name='username']",
            "password": "input[name='password']",
            "submit": "button[type='submit']",
        }
        self.fields = tools.get_selenium_elems(self.driver, selectos)
                
        self.error_message = "Invalid email or password"
        
    def tearDown(self):
    
        # Close selenium
        self.driver.quit()
        
    def redirect(self):
        """ Redirect to sign up page """
        
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/aadminn/login/")
    
    def test_valid(self):
        """ Test login with valid email and password.
        Expecting valid """
        
        # Submit form
        self.fields["username"].send_keys(self.auth_username)
        self.fields["password"].send_keys(self.password)
        self.fields["submit"].click()
        
        # Validate redirect
        self.assertNotEqual(self.driver.current_url, self.login_url)
                
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
            self.old_auth_username,
            password=self.old_password,
            is_staff=True,
        )
        
        # Create "buyers" group
        self.buyers_group = Group.objects.create(name='buyers')
        
        # Configure selenium
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Load login page
        self.login_url = self.live_server_url + "/user/sign-up/"
        self.driver.get(self.login_url)
        
        # Initial fields and data
        selectors = {
            "email": "input[name='email']",
            "password1": "input[name='password1']",
            "password2": "input[name='password2']",
            "first_name": "input[name='first-name']",
            "last_name": "input[name='last-name']",
            "submit": "button[type='submit']",
        }
        
        self.fields = tools.get_selenium_elems(self.driver, selectors)
        
        self.data = {
            "email": "test@gmail.com",
            "password_valid": "Test_pass1**",
            "password_invalid": "test_pass",
            "first_name": "Test",
            "last_name": "User",
        }
        
        # Initialize client
        self.client = Client()
    
    def tearDown(self):
    
        # Close selenium
        self.driver.quit()
        
    def redirect(self):
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
         
        # TODO
        # Validate activation email sent
    
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
            "at least one lowercase letter one uppercase letter, one number, " \
            "and one special character"
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
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".callout.callout-danger"
        ).text
        self.assertEqual(error_message, "Invalid email address")
        
        
class AdminTest(LiveServerTestCase):
    """ Validate admins custom functions """
    
    def setUp(self):
        
        # Create a user
        self.old_auth_username = "old_test_user@gmail.com"
        self.old_password = "old_test_password"
        self.auth_user = User.objects.create_user(
            self.old_auth_username,
            password=self.old_password,
            is_staff=True,
        )
        
        # Create "buyers" group
        self.buyers_group = Group.objects.create(name='buyers')
        
        # Configure selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Load login page
        self.login_url = self.live_server_url + "/user/sign-up/"
        self.driver.get(self.login_url)
        
        # Initial fields and data
        selectors = {
            "email": "input[name='email']",
            "password1": "input[name='password1']",
            "password2": "input[name='password2']",
            "first_name": "input[name='first-name']",
            "last_name": "input[name='last-name']",
            "submit": "button[type='submit']",
        }
        
        self.fields = tools.get_selenium_elems(self.driver, selectors)
        
        self.data = {
            "email": "test@gmail.com",
            "password_valid": "Test_pass1**",
            "password_invalid": "test_pass",
            "first_name": "Test",
            "last_name": "User",
        }
        
        # Initialize client
        self.client = Client()
        
    def test_redirect_accounts_profile(self):
        """ Test redirect to admin page """
        
        response = self.client.get("/accounts/profile/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")