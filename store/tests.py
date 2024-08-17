import json
from time import sleep

from django.contrib.auth.models import User
from django.utils import timezone
from django.test import LiveServerTestCase, TestCase
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from store import models
from utils.automation import get_selenium_elems


class FutureStockTestCase(TestCase):
    
    def setUp(self):
        """ Create initial data """
        
        # Create user
        self.user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com",
            is_active=True,
            is_staff=True,
        )
        
        # Create future stock
        self.today = timezone.now()
        self.tomorrow = self.today + timezone.timedelta(days=1)
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.tomorrow,
            added=False,
            amount=100,
        )
        self.endpoint = f"/api/store/next-future-stock/{self.user.email}"
        self.tomorrow_seconds = (self.tomorrow - self.today).total_seconds()
    
    def test_get(self):
        """ Test get next future stock """
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertTrue(
            json_data["next_future_stock"] <= self.tomorrow_seconds + 10 * 60
        )
        self.assertTrue(
            json_data["next_future_stock"] + 2 > self.tomorrow_seconds + 10 * 60
        )
        self.assertFalse(json_data["already_subscribed"])

    def test_get_already_added(self):
        """ Test when future stock is already added and
        no more future stock to add """
        
        self.future_stock.added = True
        self.future_stock.save()
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertEqual(json_data["next_future_stock"], 0)
        self.assertFalse(json_data["already_subscribed"])
        
    def test_get_email(self):
        """ Test get next future stock with email endpoint """
        
        response = self.client.get(f"{self.endpoint}")
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertTrue(
            json_data["next_future_stock"] <= self.tomorrow_seconds + 10 * 60
        )
        self.assertTrue(
            json_data["next_future_stock"] + 2 > self.tomorrow_seconds + 10 * 60
        )
        self.assertFalse(json_data["already_subscribed"])
        
    def test_get_email_already_subscribed(self):
        """ Test get next future stock with email endpoint,
        and user is already subscribed """
        
        models.FutureStockSubscription.objects.create(
            user=self.user,
            future_stock=self.future_stock,
            active=True,
        )
        
        response = self.client.get(f"{self.endpoint}")
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertTrue(
            json_data["next_future_stock"] <= self.tomorrow_seconds + 10 * 60
        )
        self.assertTrue(
            json_data["next_future_stock"] + 2 > self.tomorrow_seconds + 10 * 60
        )
        self.assertTrue(json_data["already_subscribed"])
        
        
class CountDownAdminTestCase(LiveServerTestCase):
    
    def setUp(self):
        """ Create initial data """
        
        # Auth user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            email=self.auth_username,
            is_staff=True,
        )
        
        # Future stock
        self.today = timezone.now()
        self.tomorrow = self.today + timezone.timedelta(days=2, seconds=10)
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.tomorrow,
            added=False,
            amount=100,
        )
        
        # Setup chrome instance
        chrome_options = Options()
        if settings.TEST_HEADLESS:
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
        fields_login = get_selenium_elems(self.driver, selectors_login)
        
        # Login
        fields_login["username"].send_keys(self.auth_username)
        fields_login["password"].send_keys(self.password)
        fields_login["submit"].click()
        
        # Wait after login
        sleep(3)
        
    def __validate_sweet_alert__(self, title, body):
        """ Validate sweet alert """
        
        # Get sweet alert
        selectors = {
            "title": ".swal2-title",
            "body": ".swal2-title + div",
        }
        sweet_alert_elems = get_selenium_elems(self.driver, selectors)
        self.assertEqual(sweet_alert_elems["title"].text, title)
        self.assertEqual(sweet_alert_elems["body"].text, body)
        
    def test_countdown(self):
        """ Login and validate count down values """
        
        self.__login__()
        inputs = get_selenium_elems(self.driver, self.selectors)
                
        # Valdiate count down values
        self.assertEqual(inputs["title"].text, "New sets coming soon!")
        self.assertEqual(inputs["days"].text, "02")
        self.assertEqual(inputs["hours"].text, "00")
        self.assertEqual(inputs["minutes"].text, "10")
        self.assertTrue(int(inputs["seconds"].text) <= 59)
        
    def test_countdown_no_future_stock(self):
        """ Login and validate count down value in 0 """
        
        # Delete future stock
        self.future_stock.delete()
        
        self.__login__()
        inputs = get_selenium_elems(self.driver, self.selectors)
        
        # Valdiate count down values
        self.assertEqual(inputs["title"].text, "New sets are available now!")
        self.assertEqual(inputs["days"].text, "00")
        self.assertEqual(inputs["hours"].text, "00")
        self.assertEqual(inputs["minutes"].text, "00")
        self.assertEqual(inputs["seconds"].text, "00")
    
    def test_notify_me_button(self):
        """ Click in notify button and validation subscription in db """
        
        self.__login__()
        
        # Click in notify me button
        selector = "#actionButtonNotify"
        self.driver.find_element(By.CSS_SELECTOR, selector).click()
        sleep(1)
        
        # Validate subscription created
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 1)
        
        subscription = subscriptions[0]
        self.assertEqual(subscription.user, self.auth_user)
        self.assertEqual(subscription.future_stock, self.future_stock)
        self.assertTrue(subscription.active)
        self.assertFalse(subscription.notified)
        
        # Validate sweet alert
        self.__validate_sweet_alert__(
            "Subscription successful",
            "You will be notified by email when new sets are available",
        )
        
    def test_notify_me_button_resubscribe(self):
        """ Click in notify button for second time, and validation subscription in db """
        
        self.__login__()
        
        selectors = {
            "notify": "#actionButtonNotify",
            "unsubscribe": "#actionButtonUnsubscribe",
            "sweet_alert_ok": '.swal2-confirm'
        }
        
        # Click in buttons
        buttons_order = [
            selectors["notify"],
            selectors["sweet_alert_ok"],
            selectors["unsubscribe"],
            selectors["sweet_alert_ok"],
            selectors["notify"],
        ]
        for button in buttons_order:
            self.driver.find_element(By.CSS_SELECTOR, button).click()
            sleep(2)
        
        # Validate subscription created
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 1)
        
        subscription = subscriptions[0]
        self.assertEqual(subscription.user, self.auth_user)
        self.assertEqual(subscription.future_stock, self.future_stock)
        self.assertTrue(subscription.active)
        self.assertFalse(subscription.notified)
        
        # Validate sweet alert
        self.__validate_sweet_alert__(
            "Subscription successful",
            "You will be notified by email when new sets are available",
        )
    
    def test_unsubscribe_button(self):
        """ Click in unsubscribe button and validation subscription in db """
        
        # Presubscribe
        models.FutureStockSubscription.objects.create(
            user=self.auth_user,
            future_stock=self.future_stock,
            active=True,
        )
        
        self.__login__()
        
        # Click in notify me button
        selector = "#actionButtonUnsubscribe"
        self.driver.find_element(By.CSS_SELECTOR, selector).click()
        sleep(1)
        
        # Validate subscription created
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 1)
        
        subscription = subscriptions[0]
        self.assertEqual(subscription.user, self.auth_user)
        self.assertEqual(subscription.future_stock, self.future_stock)
        self.assertFalse(subscription.active)
        self.assertFalse(subscription.notified)
        
        # Validate sweet alert
        self.__validate_sweet_alert__(
            "Unsubscription successful",
            "You will no longer receive notifications by email",
        )
        
        
class FutureStockSubscriptionTestCase(TestCase):
    
    def setUp(self):
        """ Create initial data """
        
        # Auth user
        self.auth_username = "test_user@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            email=self.auth_username,
            is_staff=True,
        )
        
        # Future stock
        self.today = timezone.now()
        self.tomorrow = self.today + timezone.timedelta(days=1)
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.tomorrow,
            amount=100,
        )
        
        self.endpoint = "/api/store/future-stock-subscription/"
        
    def test_invalid_subscription_type(self):
        """ Send invalid subscription type
        (only 'add' and 'remove' are allowed) """
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": self.auth_username,
                "type": "invalid",
            }),
            content_type="application/json"
        )
        
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 0)
        self.assertEqual(res.status_code, 400)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Invalid subscription type")
        
    def test_future_stock_not_found(self):
        """ Send a future stock that does not exist """
        
        # Delete future stock
        self.future_stock.delete()
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": self.auth_username,
                "type": "add",
            }),
            content_type="application/json"
        )
        
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 0)
        self.assertEqual(res.status_code, 404)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Future stock not found")
        
    def test_add_subscription(self):
        """ Add a subscription """
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": self.auth_username,
                "type": "add",
            }),
            content_type="application/json"
        )
        
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(subscriptions.count(), 1)
        self.assertEqual(subscriptions[0].user, self.auth_user)
        self.assertEqual(subscriptions[0].future_stock, self.future_stock)
        self.assertTrue(subscriptions[0].active)
        self.assertFalse(subscriptions[0].notified)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Subscribed to future stock")
        
    def test_add_subscription_new_user(self):
        """ Add a subscription with a new user """
        
        user_email = "newuser@email.com"
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": user_email,
                "type": "add",
            }),
            content_type="application/json"
        )
        
        # Validate user created
        users = User.objects.filter(email=user_email)
        user = users[0]
        print(user_email)
        self.assertEqual(users.count(), 1)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.username, user_email)
        self.assertEqual(user.email, user_email)
        
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(subscriptions.count(), 1)
        self.assertEqual(subscriptions[0].user, user)
        self.assertEqual(subscriptions[0].future_stock, self.future_stock)
        self.assertTrue(subscriptions[0].active)
        self.assertFalse(subscriptions[0].notified)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Subscribed to future stock")
    
    def test_add_subscription_already_subscribed(self):
        """ Add a subscription that is already subscribed """

        # Create subscription
        models.FutureStockSubscription.objects.create(
            user=self.auth_user,
            future_stock=self.future_stock,
            active=True,
        )
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": self.auth_username,
                "type": "add",
            }),
            content_type="application/json"
        )
        
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(subscriptions.count(), 1)
        self.assertEqual(subscriptions[0].user, self.auth_user)
        self.assertEqual(subscriptions[0].future_stock, self.future_stock)
        self.assertTrue(subscriptions[0].active)
        self.assertFalse(subscriptions[0].notified)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Subscribed to future stock")
        
    def test_remove_subscription(self):
        """ Remove a subscription """
        
        # Add subscription
        subscription = models.FutureStockSubscription.objects.create(
            user=self.auth_user,
            future_stock=self.future_stock,
        )
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": self.auth_username,
                "type": "remove",
            }),
            content_type="application/json"
        )
        
        subscription.refresh_from_db()
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(subscriptions.count(), 1)
        self.assertFalse(subscription.active)
        self.assertFalse(subscription.notified)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Unsubscribed from future stock")
    
    def test_remove_subscription_not_found(self):
        """ Remove a subscription that does not exist """
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({
                "email": self.auth_username,
                "type": "remove",
            }),
            content_type="application/json"
        )
        
        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(subscriptions.count(), 0)
        
        # Validate message
        self.assertEqual(res.json()["message"], "Subscription not found")
        
    