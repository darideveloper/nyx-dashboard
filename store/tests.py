import os
from django.test import TestCase
from store import models
from django.utils import timezone
from django.test import LiveServerTestCase
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from time import sleep
from user import tools


# Environment variables
load_dotenv()
TEST_HEADLESS = os.getenv("TEST_HEADLESS") == "True"


class FutureStockTestCase(TestCase):
    
    def setUp(self):
        """ Create initial data """
        self.today = timezone.now()
        self.tomorrow = self.today + timezone.timedelta(days=1)
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.tomorrow,
            added=False,
            amount=100,
        )
        self.endpoint = "/api/store/next-future-stock/"
    
    def test_get_next_future_stock(self):
        """ Test get next future stock """
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        tomorrow_seconds = (self.tomorrow - self.today).total_seconds()
        self.assertTrue(json_data["next_future_stock"] <= tomorrow_seconds)
        self.assertTrue(json_data["next_future_stock"] + 2 > tomorrow_seconds)

    def test_get_next_future_stock_with_added(self):
        """ Test when future stock is already added and
        no more future stock to add """
        
        self.future_stock.added = True
        self.future_stock.save()
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["next_future_stock"], 0)
        
        
class CountDownAdminTestCase(LiveServerTestCase):
    
    def setUp(self):
        """ Create initial data """
        
        # Auth user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
        )
        
        # Future stock
        self.today = timezone.now()
        self.tomorrow = self.today + timezone.timedelta(days=2)
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.tomorrow,
            added=False,
            amount=100,
        )
        
        # Setup chrome instance
        chrome_options = Options()
        if TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Test variables
        self.selectors = {
            "title": '.countdown h2',
            "days": '.counter-item:nth-child(1) span:nth-child(1)',
            "hours": '.counter-item:nth-child(2) span:nth-child(1)',
            "minutes": '.counter-item:nth-child(3) span:nth-child(1)',
            "seconds": '.counter-item:nth-child(4) span:nth-child(1)',
        }
        
    def tearDown(self):
        """ Close selenium """
        try:
            self.driver.quit()
        except Exception:
            pass
        
    def __login__(self):
        """ Login with user and password """
        
        # Load page and get inputs
        self.driver.get(f"{self.live_server_url}/admin")
        selectors_login = {
            "username": "input[name='username']",
            "password": "input[name='password']",
            "submit": "button[type='submit']",
        }
        fields_login = tools.get_selenium_elems(self.driver, selectors_login)
        
        # Login
        fields_login["username"].send_keys(self.auth_username)
        fields_login["password"].send_keys(self.password)
        fields_login["submit"].click()
        
        # Wait after login
        sleep(3)
        
    def test_countdown(self):
        """ Login and validate count down values """
        
        self.__login__()
        inputs = tools.get_selenium_elems(self.driver, self.selectors)
        
        # Valdiate count down values
        self.assertEqual(inputs["title"].text, "New sets coming soon!")
        self.assertEqual(inputs["days"].text, "01")
        self.assertEqual(inputs["hours"].text, "23")
        self.assertEqual(inputs["minutes"].text, "59")
        self.assertTrue(int(inputs["seconds"].text) <= 59)
        
    def test_countdown_no_future_stock(self):
        """ Login and validate count down value in 0 """
        
        # Delete future stock
        self.future_stock.delete()
        
        self.__login__()
        inputs = tools.get_selenium_elems(self.driver, self.selectors)
        
        # Valdiate count down values
        self.assertEqual(inputs["title"].text, "New sets coming soon!")
        self.assertEqual(inputs["days"].text, "00")
        self.assertEqual(inputs["hours"].text, "00")
        self.assertEqual(inputs["minutes"].text, "00")
        self.assertEqual(inputs["seconds"].text, "00")
        
        
        
        