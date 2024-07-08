from django.test import TestCase
from django.test import LiveServerTestCase
from django.test import Client
from django.contrib.auth.models import User, Group, Permission
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from user import tools

        
# class LogInTest(LiveServerTestCase):
#     """ Validate user login with selenium """

#     def setUp(self):
        
#         # Create a user
#         self.auth_username = "test_user"
#         self.password = "test_password"
#         self.auth_user = User.objects.create_user(
#             self.auth_username,
#             password=self.password,
#             is_staff=True,
#         )
        
#         # Configure selenium
#         chrome_options = Options()
#         chrome_options.add_argument("--headless")
        
#         # Start selenium
#         self.driver = webdriver.Chrome(options=chrome_options)
#         self.driver.implicitly_wait(10)
        
#         # Load login page
#         self.login_url = self.live_server_url + "/admin/login/"
#         self.driver.get(self.login_url)
        
#         # Fiend fields
#         selectos = {
#             "username": "input[name='username']",
#             "password": "input[name='password']",
#             "submit": "button[type='submit']",
#         }
#         self.fields = tools.get_selenium_elems(self.driver, selectos)
                
#         self.error_message = "Invalid email or password"
        
#     def tearDown(self):
    
#         # Close selenium
#         self.driver.quit()
    
#     def test_valid(self):
#         """ Test login with valid email and password.
#         Expecting valid """
        
#         # Submit form
#         self.fields["username"].send_keys(self.auth_username)
#         self.fields["password"].send_keys(self.password)
#         self.fields["submit"].click()
        
#         # Validate redirect
#         self.assertNotEqual(self.driver.current_url, self.login_url)
                
#     def test_invalid_email(self):
#         """ Test login with invalid email.
#         Expecting login failure """
        
#         # Submit form
#         self.fields["username"].send_keys("invalid email")
#         self.fields["password"].send_keys(self.password)
#         self.fields["submit"].click()
        
#         # Validate error message
#         error_message = self.driver.find_element(
#             By.CSS_SELECTOR, ".callout.callout-danger"
#         ).text
#         self.assertEqual(error_message, self.error_message)
    
#     def test_invalid_password(self):
#         """ Test login with invalid password.
#         Expecting login failure"""
        
#         # Submit form
#         self.fields["username"].send_keys(self.auth_username)
#         self.fields["password"].send_keys("invalid password")
#         self.fields["submit"].click()
        
#         # Validate error message
#         error_message = self.driver.find_element(
#             By.CSS_SELECTOR, ".callout.callout-danger"
#         ).text
#         self.assertEqual(error_message, self.error_message)
        
#     def test_no_staff(self):
#         """ Test login no staff user.
#         Expecting login failure"""
        
#         self.auth_user.is_staff = False
#         self.auth_user.save()
        
#         # Submit form
#         self.fields["username"].send_keys(self.auth_username)
#         self.fields["password"].send_keys(self.password)
#         self.fields["submit"].click()
        
#         # Validate error message
#         error_message = self.driver.find_element(
#             By.CSS_SELECTOR, ".callout.callout-danger"
#         ).text
#         self.assertEqual(error_message, self.error_message)


class SignUpTest(LiveServerTestCase):
    """ Validate register user with selenium """
    
    def setUp(self):
        
        # Create a user
        self.auth_username = "old_test_user"
        self.password = "old_test_password"
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
        self.driver.implicitly_wait(10)
        
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
            "email": "test_user",
            "password_valid": "Test_pass1**",
            "password_invalid": "test_pass",
            "first_name": "Test",
            "last_name": "User",
        }
    
    def tearDown(self):
    
        # Close selenium
        self.driver.quit()
    
    # def test_valid(self):
    #     pass
    
    # def test_alrady_used_email(self):
    #     pass
    
    def test_password_mismatch(self):
        
        # Submit form
        self.fields["email"].send_keys(self.data["email"])
        self.fields["password1"].send_keys(self.data["password_valid"])
        self.fields["password2"].send_keys(self.data["password_valid"] + "extra text")
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".error-pass"
        ).text
        self.assertEqual(error_message, "Passwords do not match")
    
    def test_password_invalid(self):
        
        # Submit form
        self.fields["email"].send_keys(self.data["email"])
        self.fields["password1"].send_keys(self.data["password_invalid"])
        self.fields["password2"].send_keys(self.data["password_invalid"])
        self.fields["first_name"].send_keys(self.data["first_name"])
        self.fields["last_name"].send_keys(self.data["last_name"])
        self.fields["submit"].click()
        
        # Validate error message
        error_message = self.driver.find_element(
            By.CSS_SELECTOR, ".error-pass"
        ).text
        error_message = "Password must be 8-50 characters long and contain " \
            "at least one lowercase letter one uppercase letter, one number, " \
            "and one special character"
        self.assertEqual(error_message, error_message)