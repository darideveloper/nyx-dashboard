import os
import json
from time import sleep

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from django.test import LiveServerTestCase, TestCase

import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from store import models
from utils.automation import get_selenium_elems


class CountDownAdminTest(LiveServerTestCase):

    def setUp(self):
        """Create initial data"""

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
            "title": ".countdown h2",
            "days": ".counter-item:nth-child(1) span:nth-child(1)",
            "hours": ".counter-item:nth-child(2) span:nth-child(1)",
            "minutes": ".counter-item:nth-child(3) span:nth-child(1)",
            "seconds": ".counter-item:nth-child(4) span:nth-child(1)",
            "btn": "#actionButtonBuy",
        }

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def __login__(self):
        """Login with user and password"""

        # Load page and get inputs
        self.driver.get(f"{self.live_server_url}/admin/")
        sleep(2)
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
        """Validate sweet alert"""

        # Get sweet alert
        selectors = {
            "title": ".swal2-title",
            "body": ".swal2-title + div",
        }
        sweet_alert_elems = get_selenium_elems(self.driver, selectors)
        self.assertEqual(sweet_alert_elems["title"].text, title)
        self.assertEqual(sweet_alert_elems["body"].text, body)

    def __click__(self, selector: str):
        """Click an element with js

        Args:
            selector (str): element to click
        """

        code = f"document.querySelector('{selector}').click()"
        self.driver.execute_script(code)

    def test_countdown(self):
        """Login and validate count down values"""

        self.__login__()
        elems = get_selenium_elems(self.driver, self.selectors)

        # Valdiate count down values
        self.assertEqual(elems["title"].text, "New sets coming soon!")
        self.assertEqual(elems["days"].text, "02")
        self.assertEqual(elems["hours"].text, "00")
        self.assertIn(elems["minutes"].text, ["10", "09"])
        self.assertTrue(int(elems["seconds"].text) <= 59)

    def test_countdown_no_future_stock(self):
        """Login and validate count down value in 0"""

        # Delete future stock
        self.future_stock.delete()

        self.__login__()
        elems = get_selenium_elems(self.driver, self.selectors)

        # Valdiate count down values
        self.assertEqual(elems["days"].text, "00")
        self.assertEqual(elems["hours"].text, "00")
        self.assertEqual(elems["minutes"].text, "00")
        self.assertEqual(elems["seconds"].text, "00")
        self.assertEqual(elems["title"].text, "New sets are available now!")
        self.assertEqual(elems["btn"].text, "No Sets Left")

    def test_notify_me_button(self):
        """Click in notify button and validation subscription in db"""

        self.__login__()

        # Click in notify me button
        selector = "#actionButtonNotify"
        self.__click__(selector)
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
        """Click in notify button for second time, and validation subscription in db"""

        self.__login__()

        selectors = {
            "notify": "#actionButtonNotify",
            "unsubscribe": "#actionButtonUnsubscribe",
            "sweet_alert_ok": ".swal2-confirm",
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
            self.__click__(button)
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
        """Click in unsubscribe button and validation subscription in db"""

        # Presubscribe
        models.FutureStockSubscription.objects.create(
            user=self.auth_user,
            future_stock=self.future_stock,
            active=True,
        )

        self.__login__()

        # Click in notify me button
        selector = "#actionButtonUnsubscribe"
        self.__click__(selector)
        sleep(2)

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

    def test_countdown_no_stock(self):
        """Login and validate count down value 0 sets left in stock"""

        # Delete future stock
        self.future_stock.delete()

        # Set stock valur to 0
        models.StoreStatus.objects.create(
            key="current_stock",
            value=0,
        )

        self.__login__()
        elems = get_selenium_elems(self.driver, self.selectors)

        # Valdiate count down values
        self.assertEqual(elems["title"].text, "New sets are available now!")
        self.assertEqual(elems["btn"].text, "No Sets Left")


class FutureStockSubscriptionViewTest(TestCase):

    def setUp(self):
        """Create initial data"""

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
        """Send invalid subscription type
        (only 'add' and 'remove' are allowed)"""

        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": self.auth_username,
                    "type": "invalid",
                }
            ),
            content_type="application/json",
        )

        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 0)
        self.assertEqual(res.status_code, 400)

        # Validate message
        self.assertEqual(res.json()["message"], "Invalid subscription type")

    def test_future_stock_not_found(self):
        """Send a future stock that does not exist"""

        # Delete future stock
        self.future_stock.delete()

        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": self.auth_username,
                    "type": "add",
                }
            ),
            content_type="application/json",
        )

        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(subscriptions.count(), 0)
        self.assertEqual(res.status_code, 404)

        # Validate message
        self.assertEqual(res.json()["message"], "Future stock not found")

    def test_add_subscription(self):
        """Add a subscription"""

        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": self.auth_username,
                    "type": "add",
                }
            ),
            content_type="application/json",
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
        """Add a subscription with a new user"""

        user_email = "newuser@email.com"
        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": user_email,
                    "type": "add",
                }
            ),
            content_type="application/json",
        )

        # Validate user created
        users = User.objects.filter(email=user_email)
        user = users[0]
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
        """Add a subscription that is already subscribed"""

        # Create subscription
        models.FutureStockSubscription.objects.create(
            user=self.auth_user,
            future_stock=self.future_stock,
            active=True,
        )

        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": self.auth_username,
                    "type": "add",
                }
            ),
            content_type="application/json",
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
        """Remove a subscription"""

        # Add subscription
        subscription = models.FutureStockSubscription.objects.create(
            user=self.auth_user,
            future_stock=self.future_stock,
        )

        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": self.auth_username,
                    "type": "remove",
                }
            ),
            content_type="application/json",
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
        """Remove a subscription that does not exist"""

        res = self.client.post(
            self.endpoint,
            data=json.dumps(
                {
                    "email": self.auth_username,
                    "type": "remove",
                }
            ),
            content_type="application/json",
        )

        subscriptions = models.FutureStockSubscription.objects.all()
        self.assertEqual(res.status_code, 404)
        self.assertEqual(subscriptions.count(), 0)

        # Validate message
        self.assertEqual(res.json()["message"], "Subscription not found")


class SaleAdminListTest(LiveServerTestCase):
    """Validate buyers custom functions in sale list view"""

    def setUp(self):

        # Create a user
        self.auth_username = "test@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username,
            password=self.password,
            is_staff=True,
            first_name="first",
            last_name="last",
            email="test@mail.com",
        )

        # Create second user
        self.auth_user_2 = User.objects.create_user(
            "user_2",
            password="pass_2",
            is_staff=True,
            first_name="first",
            last_name="last",
            email="test2@mail.com",
        )

        # Create "buyers" group
        buyers_group = Group.objects.create(name="buyers")
        view_sale_perm = Permission.objects.get(codename="view_sale")
        buyers_group.permissions.add(view_sale_perm)

        # Add permision to only see sale model
        self.auth_user.groups.add(buyers_group)
        self.auth_user.save()

        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Create sales
        set = models.Set.objects.create(
            name="set name", points=5, price=275, recommended=False, logos=5
        )
        colors_num = models.ColorsNum.objects.create(
            num=4, price=20, details="4 Colors (Trackers and 3 logo colors) +20USD"
        )
        color = models.Color.objects.create(name="blue")
        status = models.SaleStatus.objects.create(value="Pending")
        promo_code_type = models.PromoCodeType.objects.create(name="amount")
        promo_code = models.PromoCode.objects.create(
            code="sample-promo",
            discount=100,
            type=promo_code_type,
        )

        models.Sale.objects.create(
            user=self.auth_user,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
            promo_code=promo_code,
        )

        models.Sale.objects.create(
            user=self.auth_user_2,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country 2",
            state="test state 2",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
            promo_code=promo_code,
        )

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def __login__(self):
        """Login with valid user and password"""

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
        sleep(3)

        # go to sales page
        self.driver.get(self.live_server_url + "/admin/store/sale/")
        sleep(0.1)

    def __login_admin__(self):
        """Change the user to admin and login"""

        self.auth_user.is_superuser = True
        self.auth_user.save()

        self.__login__()

    def test_hide_filters_buyer(self):
        """Check removed filters for buyer user"""

        self.__login__()

        selectors_filters = {
            "user": 'select[data-name="user"]',
            "country": 'select[data-name="country"]',
            "state": 'select[data-name="state"]',
            "promo_code": 'select[data-name="promo_code"]',
        }
        filters = get_selenium_elems(self.driver, selectors_filters)
        for filter in filters.values():
            self.assertIsNone(filter)

    def test_no_hide_filters_admin(self):
        """Check no removed filters for admin user"""

        self.__login_admin__()

        selectors_filters = {
            "user": 'select[data-name="user"]',
            "country": 'select[data-name="country"]',
            "state": 'select[data-name="state"]',
            "promo_code": 'select[data-name="promo_code"]',
        }
        filters = get_selenium_elems(self.driver, selectors_filters)
        for filter in filters.values():
            self.assertIsNotNone(filter)

    def test_hide_user_colum_buyer(self):
        """Check removed user column for buyer user"""

        self.__login__()

        # Index 2 in buyer view because missing checkboxes
        selectors = {
            "th_user": "th:nth-child(2)",
        }
        elems = get_selenium_elems(self.driver, selectors)

        # Validate user column is hidden
        self.assertNotEqual(elems["th_user"].text, "User")

    def test_no_hide_user_colum_admin(self):
        """Check no removed user column for admin user"""

        self.__login_admin__()

        # Index 3 in buyer view because checkboxes
        selectors = {
            "th_user": "th:nth-child(3)",
        }
        elems = get_selenium_elems(self.driver, selectors)

        # Validate user column is hidden
        self.assertEqual(elems["th_user"].text, "User")

    def test_hide_sales_buyer(self):
        """Check removed other users orders/sales"""

        self.__login__()

        # Index 2 in buyer view because missing checkboxes
        selector_row = "#result_list td:nth-child(3)"
        rows = self.driver.find_elements(By.CSS_SELECTOR, selector_row)

        # Validate user column is hidden
        self.assertEqual(len(rows), 1)

    def test_no_hide_sales_admin(self):
        """Check no removed other users orders/sales"""

        self.__login_admin__()

        # Index 2 in buyer view because missing checkboxes
        selector_row = "#result_list td:nth-child(3)"
        rows = self.driver.find_elements(By.CSS_SELECTOR, selector_row)

        # Validate user column is hidden
        self.assertEqual(len(rows), 2)


class SaleAdminChangeTest(LiveServerTestCase):
    """Validate buyers custom functions in sale change view"""

    def setUp(self):

        # Create a user
        self.auth_username = "test@gmail.com"
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
        buyers_group = Group.objects.create(name="buyers")
        view_sale_perm = Permission.objects.get(codename="view_sale")
        buyers_group.permissions.add(view_sale_perm)

        # Add permision to only see sale model
        self.auth_user.groups.add(buyers_group)
        self.auth_user.save()

        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Create sales
        set = models.Set.objects.create(
            name="set name", points=5, price=275, recommended=False, logos=5
        )
        colors_num = models.ColorsNum.objects.create(
            num=4, price=20, details="4 Colors (Trackers and 3 logo colors) +20USD"
        )
        color = models.Color.objects.create(name="blue")
        status = models.SaleStatus.objects.create(value="Pending")
        promo_code_type = models.PromoCodeType.objects.create(name="amount")
        promo_code = models.PromoCode.objects.create(
            code="sample-promo",
            discount=100,
            type=promo_code_type,
        )

        self.sale = models.Sale.objects.create(
            user=self.auth_user,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
            promo_code=promo_code,
        )

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def __login__(self):
        """Login with valid user and password"""

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
        sleep(3)

        # go to sales change page
        link = f"{self.live_server_url}/admin/store/sale/{self.sale.id}/change/"
        self.driver.get(link)
        sleep(0.1)

    def __login_admin__(self):
        """Change the user to admin and login"""

        self.auth_user.is_superuser = True
        self.auth_user.save()

        self.__login__()

    def test_no_href_buyer(self):
        """Validate no href attribute in links of view for buyer user"""

        self.__login__()

        # Get all links
        links = self.driver.find_elements(By.TAG_NAME, "#sale_form a")

        # Validate all links
        for link in links:
            self.assertEqual(link.get_attribute("href"), None)

    def test_href_admin(self):
        """Validate href attribute in links of view for admin user"""

        self.__login_admin__()

        # Get all links
        links = self.driver.find_elements(By.TAG_NAME, "#sale_form a")

        # Validate all links
        for link in links:
            self.assertNotEqual(link.get_attribute("href"), None)


class SaleModelTest(TestCase):
    """Test custom actions of sale model"""

    def setUp(self):

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com", password="test_password", email="test@gmail.com"
        )

        # Create status with a command
        call_command("apps_loaddata")

        # Get sale data
        set = models.Set.objects.all().first()
        colors_num = models.ColorsNum.objects.all().first()
        color = models.Color.objects.all().first()
        status = models.SaleStatus.objects.get(value="Pending")

        self.sale = models.Sale.objects.create(
            user=self.auth_user,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
        )

    def test_create_custom_id(self):
        """Create custom id for sale"""

        # Validate custom id
        self.assertEqual(len(self.sale.id), 12)

    def test_change_status_email(self):
        """Send email to client when change status"""

        # Update sale status
        status_delivered = models.SaleStatus.objects.get(value="Delivered")
        self.sale.status = status_delivered
        self.sale.save()

        # Validate email sent
        self.assertEqual(len(mail.outbox), 1)

        # Validate email content
        subject = f"Order {self.sale.id} {status_delivered.value}"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        cta_link_base = f"{settings.HOST}/admin/"
        self.assertIn(cta_link_base, email_html)

    def test_change_status_no_email(self):
        """Status change email not sent because of a excluded status"""

        # Update sale status
        status_excluded = models.SaleStatus.objects.get(value="Reminder Sent")
        self.sale.status = status_excluded
        self.sale.save()

        # Validate email sent
        self.assertEqual(len(mail.outbox), 0)

    def test_change_status_tracking_number(self):
        """Set status to shipped when tracking number is added"""

        # Add tracking number
        tracking_number = "123456"
        self.sale.tracking_number = tracking_number
        self.sale.save()

        # Validate status
        self.assertEqual(self.sale.status.value, "Shipped")

    def test_send_email_tracking_number(self):
        """Send email when tracking number changes"""

        # Add tracking number
        tracking_number = "123456"
        self.sale.tracking_number = tracking_number
        self.sale.save()

        # Validate status
        self.assertEqual(self.sale.status.value, "Shipped")

        # Validate email content
        subject = f"Tracking number added to your order {self.sale.id}"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        cta_link_base = self.sale.tracking_number
        self.assertIn(cta_link_base, email_html)
        self.assertIn(tracking_number, email_html)

    def keep_status_no_email(self):
        """No send email when save sale without status change"""

        self.sale.save()

        # Validate email sent
        self.assertEqual(len(mail.outbox), 0)


class SaleAdminExportExcel(LiveServerTestCase):

    def setUp(self):
        """Create initial data"""

        # Create a user
        self.username = "test_user"
        self.password = "test_password_123**"
        self.auth_user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="test@gmail.com",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )

        # Paths
        self.download_path = os.path.join(settings.BASE_DIR, "store", "test_files")
        os.makedirs(self.download_path, exist_ok=True)
        self.initial_files = os.listdir(self.download_path)

        # Create status with a command
        call_command("apps_loaddata")

        # Start selenium
        self.__setup_chrome__()

        # Create 2 sales
        self.sales = []
        for _ in range(2):
            sale = self.__create_sale__()
            self.sales.append(sale)

        # Login
        self.__login__()

        # Global selectors
        self.selectors = {
            "row": '#result_list [role="row"]',
            "checkbox_select": 'input[type="checkbox"]',
            "checkbox_select_all": "#action-toggle",
            "actions_select": 'select[name="action"]',
            "submit": 'button[type="submit"][name="index"]',
            "error": ".alert-warning",
        }

    def __create_sale__(self) -> models.Sale:
        """Create a sale with specific data to a specific user

        Returns:
            models.Sale: Sale nbj
        """

        # Sale foreign keys
        set = models.Set.objects.all().first()
        colors_num = models.ColorsNum.objects.all().first()
        color = models.Color.objects.all().first()
        status = models.SaleStatus.objects.get(value="Pending")

        # Create sale
        sale = models.Sale.objects.create(
            user=self.auth_user,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
        )

        # Add logo to sale
        current_path = os.path.dirname(os.path.abspath(__file__))
        test_files_folder = os.path.join(current_path, "test_files")
        logo_path = os.path.join(test_files_folder, "logo.png")
        logo = SimpleUploadedFile(
            name="logo.png",
            content=open(logo_path, "rb").read(),
            content_type="image/png",
        )
        sale.logo = logo
        sale.save()

        return sale

    def __setup_chrome__(self):
        """Start selenium"""

        # Setup options
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Setup download path
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": self.download_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )

        # Setup driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

    def __login__(self):
        """Login with valid user and password"""

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
        fields["username"].send_keys(self.username)
        fields["password"].send_keys(self.password)
        fields["submit"].click()
        sleep(3)

        # go to sales page
        self.driver.get(self.live_server_url + "/admin/store/sale/")
        sleep(0.1)

    def __download_excel__(self) -> str:
        """Download excel file for selected sales

        Returns:
            str: Downloaded file path
        """

        # Select export action with js
        script = """
            document.querySelector('[name="action"]').value = "export_sale_to_excel";
            console.log(document.querySelector('[name="action"]').value);
        """
        self.driver.execute_script(script)
        sleep(2)

        # Click submit
        self.__click__(self.selectors["submit"])
        sleep(2)

        # Detect new file in download folder
        current_files = os.listdir(self.download_path)
        downloaded_files = list(
            filter(lambda file: file not in self.initial_files, current_files)
        )
        if not downloaded_files:
            return None
        downloaded_file = downloaded_files[0]
        downloaded_file_path = os.path.join(self.download_path, downloaded_file)
        return downloaded_file_path

    def __get_excel_data__(self, file_path: str) -> list[dict]:
        """Get excel data and validate header

        Args:
            file_path (str): Excel file path

        Returns:
            list[dict]: Excel data
        """

        # Get excel data
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        data = []
        for row in sheet.iter_rows(values_only=True):

            # Convert None cells to empty strings
            row = list(map(lambda cell: "" if cell is None else cell, row))
            data.append(row)

        # Validate header
        header = data[0]
        self.assertEqual(
            header,
            [
                "id",
                "estado",
                "fecha",
                "precio",
                "email",
                "set",
                "país",
                "persona",
                "comentarios",
                "link",
            ],
        )

        return data[1:]

    def __click__(self, selector: str):
        """Click on a selector

        Args:
            selector (str): Selector to click
        """

        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
        elem.click()
        sleep(1)

    def tearDown(self):
        """Close selenium"""

        # Delete all excel files in temp folder
        for file in os.listdir(self.download_path):
            if not file.endswith(".xlsx"):
                continue
            file_path = os.path.join(self.download_path, file)
            os.remove(file_path)

        # End selenium
        try:
            self.driver.quit()
        except Exception:
            pass

    def test_export_1_sale(self):
        """Export 1 sale to excel"""

        # Export to excel
        selector_row_1 = f"{self.selectors['row']}:nth-child(1)"
        selector_row_1_checkbox = (
            f"{selector_row_1} {self.selectors['checkbox_select']}"
        )
        self.__click__(selector_row_1_checkbox)
        sleep(5)
        excel_file_path = self.__download_excel__()
        data = self.__get_excel_data__(excel_file_path)

        # Validate excel rows number
        self.assertEqual(len(data), 1)

        # Validate excel file content
        for sale_excel in data:
            sale_excel = list(sale_excel)
            sale = list(filter(lambda sale: sale.id == sale_excel[0], self.sales))[0]
            sale_data = sale.get_sale_data_list()
            self.assertEqual(sale_excel, sale_data)

    def test_export_2_sales(self):
        """Export 2 sales to excel"""

        # Export to excel
        self.__click__(self.selectors["checkbox_select_all"])
        sleep(5)
        excel_file_path = self.__download_excel__()
        data = self.__get_excel_data__(excel_file_path)

        # Validate excel rows number
        self.assertEqual(len(data), 2)

        # Validate excel file content
        for sale_excel in data:
            sale_excel = list(sale_excel)
            sale = list(filter(lambda sale: sale.id == sale_excel[0], self.sales))[0]
            sale_data = sale.get_sale_data_list()
            self.assertEqual(sale_excel, sale_data)

    def test_no_sales_selected(self):
        """No export data if there are no sales selected"""

        excel_file_path = self.__download_excel__()

        # Validate no file downloaded
        self.assertIsNone(excel_file_path)

        # Validate error message in page
        error_elem = self.driver.find_element(By.CSS_SELECTOR, self.selectors["error"])
        error_text = error_elem.text.replace("x", "").strip()

        expected_text = "Items must be selected in order to perform actions on them. "
        expected_text += "No items have been changed."
        self.assertIn(expected_text, error_text)

    def test_no_export_regular_users(self):
        """Valdiate regular users without the permission to export"""

        # Set user as regular
        self.auth_user.is_superuser = False
        self.auth_user.save()

        # Create "buyers" group
        buyers_group = Group.objects.create(name="buyers")
        view_sale_perm = Permission.objects.get(codename="view_sale")
        buyers_group.permissions.add(view_sale_perm)

        # Add permision to only see sale model
        self.auth_user.groups.add(buyers_group)
        self.auth_user.save()
        sleep(2)

        # Refresh page
        self.driver.refresh()

        # Try to export with a regular user
        # Expected error because there are no actions available
        try:
            self.__download_excel__()
        except Exception:
            pass
        else:
            self.fail("Regular user should not be able to export")


class SaleAdminQuerySetTest(LiveServerTestCase):
    """Validate queryset (visible rows) in admin sale view
    for each user group
    """

    def setUp(self):

        # Create a user
        self.auth_username_1 = "test1@gmail.com"
        self.auth_username_2 = "test2@gmail.com"
        self.auth_username_3 = "test3@gmail.com"
        self.password = "test_password"
        self.auth_user = User.objects.create_user(
            self.auth_username_1,
            password=self.password,
            is_staff=True,
            first_name="first",
            last_name="last",
            email="test@mail.com",
        )

        # Create second user
        self.auth_user_2 = User.objects.create_user(
            self.auth_username_2,
            password=self.password,
            is_staff=True,
            first_name="first",
            last_name="last",
            email="test2@mail.com",
        )

        # Create third user
        self.auth_user_3 = User.objects.create_user(
            self.auth_username_3,
            password=self.password,
            is_staff=True,
            first_name="first",
            last_name="last",
            email="test3@mail.com",
        )

        # Create groups
        admins_group = Group.objects.create(name="admins")
        buyers_group = Group.objects.create(name="buyers")
        support_group = Group.objects.create(name="supports")
        view_sale_perm = Permission.objects.get(codename="view_sale")
        admins_group.permissions.add(view_sale_perm)
        buyers_group.permissions.add(view_sale_perm)
        support_group.permissions.add(view_sale_perm)

        # Add permision to users
        self.auth_user.groups.add(buyers_group)
        self.auth_user.save()

        self.auth_user_2.groups.add(admins_group)
        self.auth_user_2.save()

        self.auth_user_3.groups.add(support_group)
        self.auth_user_3.save()

        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Create sales
        set = models.Set.objects.create(
            name="set name", points=5, price=275, recommended=False, logos=5
        )
        colors_num = models.ColorsNum.objects.create(
            num=4, price=20, details="4 Colors (Trackers and 3 logo colors) +20USD"
        )
        color = models.Color.objects.create(name="blue")
        status = models.SaleStatus.objects.create(value="Pending")
        promo_code_type = models.PromoCodeType.objects.create(name="amount")
        promo_code = models.PromoCode.objects.create(
            code="sample-promo",
            discount=100,
            type=promo_code_type,
        )

        models.Sale.objects.create(
            user=self.auth_user,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
            promo_code=promo_code,
        )

        models.Sale.objects.create(
            user=self.auth_user_2,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country 2",
            state="test state 2",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
            promo_code=promo_code,
        )

        models.Sale.objects.create(
            user=self.auth_user_3,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country 3",
            state="test state 3",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
            promo_code=promo_code,
        )

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def __login__(self, username: str, password: str):
        """Login with valid user and password

        Args:
            username (str): Username to login
            password (str): Password to login
        """

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
        fields["username"].send_keys(username)
        fields["password"].send_keys(password)
        fields["submit"].click()
        sleep(3)

        # go to sales page
        self.driver.get(self.live_server_url + "/admin/store/sale/")
        sleep(0.1)

        self.selectors = {"row": '[role="row"]'}

    def test_buyer_own_sales(self):
        """Validate buyer be able to see only own sales"""

        self.__login__(self.auth_username_1, self.password)

        # Valite number of rows
        rows = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["row"])
        self.assertEqual(len(rows), 1)

    def test_admin_all_sales(self):
        """Validate admin be able to see all sales"""

        self.__login__(self.auth_username_2, self.password)

        # Valite number of rows
        rows = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["row"])
        self.assertEqual(len(rows), 3)

    def test_support_all_sales(self):
        """Validate support member be able to see all sales"""

        self.__login__(self.auth_username_3, self.password)

        # Valite number of rows
        rows = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["row"])
        self.assertEqual(len(rows), 3)
