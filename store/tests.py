import os
import json
import base64
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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from store import models
from utils.automation import get_selenium_elems


class FutureStockTest(TestCase):

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


class CountDownAdminTest(LiveServerTestCase):

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
        elems = get_selenium_elems(self.driver, self.selectors)

        # Valdiate count down values
        self.assertEqual(elems["title"].text, "New sets coming soon!")
        self.assertEqual(elems["days"].text, "02")
        self.assertEqual(elems["hours"].text, "00")
        self.assertEqual(elems["minutes"].text, "10")
        self.assertTrue(int(elems["seconds"].text) <= 59)

    def test_countdown_no_future_stock(self):
        """ Login and validate count down value in 0 """

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


class FutureStockSubscriptionTest(TestCase):

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
        self.assertEqual(res.json()["message"],
                         "Unsubscribed from future stock")

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


class SaleTest(TestCase):

    def setUp(self):
        """ Create initial data """

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com"
        )

        self.endpoint = "/api/store/sale/"
        
        # Create initial data
        call_command("apps_loaddata")
        
        # Initial data
        self.data = {
            "email": self.auth_user.email,
            "set": "basic",
            "colors_num": 4,
            "set_color": "blue",
            "logo_color_1": "white",
            "logo_color_2": "red",
            "logo_color_3": "blue",
            "logo": "",
            "included_extras": [
                "Straps",
                "Wifi 2.4ghz USB Dongle",
            ],
            "promo": {
                "code": "sample-promo",
                "discount": {
                    "type": "amount",
                    "value": 100
                }
            },
            "full_name": "dari",
            "country": "dev",
            "state": "street",
            "city": "ags",
            "postal_code": "20010",
            "street_address": "street 1",
            "phone": "12323123"
        }
        
        # Files paths
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.test_files_folder = os.path.join(current_path, "test_files")
        
        # Add current stock to store status
        self.current_stock = models.StoreStatus.objects.get(key="current_stock")
        self.current_stock.value = 100
        self.current_stock.save()

    def __get_logo_base64__(self, file_name: str) -> str:
        """ Get logo in base64 string
        
        Args:
            file_name (str): File namw inside test_files folder
            
        Returns:
            str: Base64 string
        """
        
        logo_path = os.path.join(self.test_files_folder, file_name)
        with open(logo_path, "rb") as file:
            logo_data = file.read()
            return base64.b64encode(logo_data).decode("utf-8")

    def test_sale_missing_fields(self):
        """ Save new sale but with missing fields """

        # Missing fields
        data = {
            "test": "test"
        }
        json_data = json.dumps(data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # First missing field detected
        self.assertEqual(res.json()["message"], "Missing field: email")

    def test_sale_no_logo(self):
        """ Save new sale with full data but without logo """

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        json_res = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_res["message"], "Sale saved")
        
        # Validate stripe link
        self.assertTrue(json_res["data"]["stripe_link"])
        self.assertTrue("checkout.stripe.com" in json_res["data"]["stripe_link"])

        # Validate colors
        colors = {
            "set_color": self.data["set_color"],
            "logo_color_1": self.data["logo_color_1"],
            "logo_color_2": self.data["logo_color_2"],
            "logo_color_3": self.data["logo_color_3"],
        }
        colors_objs = {}
        for color_key, color_value in colors.items():
            color_obj = models.Color.objects.filter(name=color_value)
            self.assertEqual(color_obj.count(), 1)
            colors_objs[color_key] = color_obj[0]

        # Validate promo type
        promo_data = self.data["promo"]
        promo_type = promo_data["discount"]["type"]
        promo_type_obj = models.PromoCodeType.objects.filter(name=promo_type)
        self.assertEqual(promo_type_obj.count(), 1)
        self.assertEqual(promo_type_obj[0].name, promo_type)

        # Validate promo
        promo_data = self.data["promo"]
        promo_obj = models.PromoCode.objects.filter(code=promo_data["code"])
        self.assertEqual(promo_obj.count(), 1)
        self.assertEqual(promo_obj[0].discount, promo_data["discount"]["value"])

        # Validate sale data
        sale_obj = models.Sale.objects.all()
        self.assertEqual(sale_obj.count(), 1)
        self.assertEqual(sale_obj[0].user, self.auth_user)
        self.assertEqual(sale_obj[0].set.name, self.data["set"])
        self.assertEqual(sale_obj[0].colors_num.num, self.data["colors_num"])
        self.assertEqual(sale_obj[0].color_set, colors_objs["set_color"])
        self.assertEqual(sale_obj[0].logo_color_1, colors_objs["logo_color_1"])
        self.assertEqual(sale_obj[0].logo_color_2, colors_objs["logo_color_2"])
        self.assertEqual(sale_obj[0].logo_color_3, colors_objs["logo_color_3"])
        self.assertEqual(sale_obj[0].logo, "")
        self.assertEqual(sale_obj[0].promo_code, promo_obj[0])
        self.assertEqual(sale_obj[0].full_name, self.data["full_name"])
        self.assertEqual(sale_obj[0].country, self.data["country"])
        self.assertEqual(sale_obj[0].state, self.data["state"])
        self.assertEqual(sale_obj[0].city, self.data["city"])
        self.assertEqual(sale_obj[0].postal_code, self.data["postal_code"])
        self.assertEqual(sale_obj[0].street_address, self.data["street_address"])
        self.assertEqual(sale_obj[0].phone, self.data["phone"])
        self.assertEqual(sale_obj[0].status.value, "Pending")

        # Validate total
        total = 0
        set_obj = models.Set.objects.filter(name=self.data["set"]).first()
        colors_num_obj = models.ColorsNum.objects.filter(
            num=self.data["colors_num"]
        ).first()
        addons = models.Addon.objects.filter(name__in=self.data["included_extras"])
        total += set_obj.price
        total += colors_num_obj.price
        for addon in addons:
            total += addon.price
        total -= promo_obj[0].discount
        total = round(total, 2)
        self.assertEqual(sale_obj[0].total, total)

        # Validte empty logo
        self.assertEqual(sale_obj[0].logo, "")

    def test_logo_png(self):
        """ Save sale with a logo in png """
    
        image_base64 = "data:image/png;base64,"
        image_base64 += self.__get_logo_base64__("logo.png")
            
        # Add logo to data
        self.data["logo"] = image_base64
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate logo file
        sale = models.Sale.objects.all()[0]
        self.assertTrue(sale.logo.url)
        
    def test_logo_svg(self):
        """ Save sale with a logo in svg """
    
        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += self.__get_logo_base64__("logo.svg")
            
        # Add logo to data
        self.data["logo"] = image_base64
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate logo file
        sale = models.Sale.objects.all()[0]
        self.assertTrue(sale.logo.url)

    def test_1_colors(self):
        """ Save sale with single color (set color) """
        
        # Change colors num to 1
        self.data["colors_num"] = 1
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
                
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1, None)
        self.assertEqual(sale.logo_color_2, None)
        self.assertEqual(sale.logo_color_3, None)
        
    def test_2_color(self):
        """ Save sale with set color and 1 logo color """
        
        # Change colors num to 1
        self.data["colors_num"] = 2
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2, None)
        self.assertEqual(sale.logo_color_3, None)
        
    def test_3_color(self):
        """ Save sale with set color and 2 logo colors """
        
        # Change colors num to 1
        self.data["colors_num"] = 3
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
                
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3, None)
        
    def test_4_color(self):
        """ Save sale with set color and 3 logo colors """
        
        # Change colors num to 1
        self.data["colors_num"] = 4
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
                
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3.name, self.data["logo_color_3"])
        
    def test_guest_user(self):
        """ Save new sale with a guest user """
        
        self.data["email"] = "guest_user@gmail.com"

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Sale saved")

        # Validate user created
        users = User.objects.filter(email=self.data["email"])
        self.assertEqual(users.count(), 1)
        user = users[0]
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.username, self.data["email"])
        self.assertEqual(user.email, self.data["email"])
        
        # Validate invite email sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, "Nyx Trackers Complete your registration")
        self.assertEqual(sent_email.to, [self.data["email"]])
        
        # Validate email text content
        cta_link_base = f"{settings.HOST}/sign-up/"
        sent_email = mail.outbox[0]
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        self.assertIn("Complete registration", email_html)
        
    def test_no_stock(self):
        """ Skip sale when there is no stock """
    
        # Update stock
        self.current_stock.value = "0"
        self.current_stock.save()
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)
        json_data = res.json()
        self.assertEqual(json_data["message"], "No stock available")
        self.assertEqual(json_data["status"], "error")
        self.assertEqual(json_data["data"], {})
        
        
class CurrentStockTest(TestCase):

    def setUp(self):
        """ Create initial data """
        
        # Create initial data
        call_command("apps_loaddata")
        
        self.current_stock = models.StoreStatus.objects.get(
            key="current_stock",
        )
        self.current_stock.value = 100
        self.current_stock.save()
        
        self.endpoint = "/api/store/current-stock/"
        
    def test_get(self):
        """ Get current stock """
        
        res = self.client.get(self.endpoint)
        
        # Validate response
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["message"], "Current stock")
        self.assertEqual(json_data["data"]["current_stock"], 100)
        
    def test_get_0(self):
        """ Get current stock with 0 value """
        
        # Update stock
        self.current_stock.value = "0"
        self.current_stock.save()
        
        res = self.client.get(self.endpoint)
        
        # Validate response
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["message"], "Current stock")
        self.assertEqual(json_data["data"]["current_stock"], 0)
        
        
class SaleDoneTest(TestCase):

    def setUp(self):
        """ Create initial data """

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com"
        )
        
        # Create initial data
        call_command("apps_loaddata")
        
        # Create sale
        set = models.Set.objects.all().first()
        
        colors_num = models.ColorsNum.objects.all().first()
        
        color = models.Color.objects.all().first()
        status = models.SaleStatus.objects.get(value="Pending")
        
        # Files paths
        current_path = os.path.dirname(os.path.abspath(__file__))
        test_files_folder = os.path.join(current_path, "test_files")
        
        logo_path = os.path.join(test_files_folder, "logo.png")
        
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
        
        # Add logo to sale
        logo = SimpleUploadedFile(
            name="logo.png",
            content=open(logo_path, "rb").read(),
            content_type="image/png"
        )
        self.sale.logo = logo
        self.sale.save()
        
        # Request data
        self.endpoint = "/api/store/sale-done"
        
        # Set current stock to 100
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock.value = 100
        current_stock.save()
        
        self.redirect_page = settings.LANDING_HOST
        
    def test_get(self):
        
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")
        
        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={self.sale.id}&sale-status=success"
        self.assertEqual(res.url, self.redirect_page)
        
        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Paid")
                
    def test_get_invalid_id(self):
        
        fake_id = "fake-id"
        res = self.client.get(f"{self.endpoint}/{fake_id}/")
        
        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={fake_id}&sale-status=error"
        self.assertEqual(res.url, self.redirect_page)
        
        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Pending")
    
    def test_email(self):
        """ Validate email sent content after sale confirmation """
        
        # Validate redirect
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")
        self.assertEqual(res.status_code, 302)
        
        # validate activation email sent
        self.assertEqual(len(mail.outbox), 2)
          
        # Validate email text content
        subject = "Nyx Trackers Payment Confirmation"
        cta_link_base = f"{settings.HOST}/admin/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        
        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        
        # Validate admin email
        
        # Validate email text content
        subject = "Nyx Trackers New Sale"
        cta_link_base = f"{settings.HOST}/admin/sale/{self.sale.id}/change/"
        sent_email = mail.outbox[1]
        self.assertEqual(subject, sent_email.subject)
        
        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        
        # Validate sale details
        sale_data = self.sale.get_sale_data_dict()
        for sale_key, sale_value in sale_data.items():
            self.assertIn(sale_key, email_html)
            self.assertIn(str(sale_value), email_html)
            
        # Valdate logo in email
        self.assertIn('id="extra-image"', email_html)

    def test_email_no_logo(self):
        """ Validate email sent without logo """
        
        # Remove logo from sale
        self.sale.logo = None
        self.sale.save()
        
        # Validate redirect
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")
        self.assertEqual(res.status_code, 302)
        
        # validate activation email sent
        self.assertEqual(len(mail.outbox), 2)
          
        # Validate client email
          
        # Validate email text content
        subject = "Nyx Trackers Payment Confirmation"
        cta_link_base = f"{settings.HOST}/admin/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        
        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        
        # Validate sale details
        sale_data = self.sale.get_sale_data_dict()
        for sale_key, sale_value in sale_data.items():
            self.assertIn(sale_key, email_html)
            self.assertIn(str(sale_value), email_html)
            
        # Valdate logo in email
        self.assertNotIn('id="extra-image"', email_html)
        
        
class AdminBuyerSaleListTest(LiveServerTestCase):
    """ Validate buyers custom functions in sale list view """
    
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
        buyers_group = Group.objects.create(name='buyers')
        view_sale_perm = Permission.objects.get(codename='view_sale')
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
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Create sales
        set = models.Set.objects.create(
            name="set name",
            points=5,
            price=275,
            recommended=False,
            logos=5
        )
        colors_num = models.ColorsNum.objects.create(
            num=4,
            price=20,
            details="4 Colors (Trackers and 3 logo colors) +20USD"
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
        
        # go to sales page
        self.driver.get(self.live_server_url + "/admin/store/sale/")
        sleep(0.1)
        
    def __login_admin__(self):
        """ Change the user to admin and login """
        
        self.auth_user.is_superuser = True
        self.auth_user.save()
        
        self.__login__()
        
    def test_hide_filters_buyer(self):
        """ Check removed filters for buyer user """
        
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
        """ Check no removed filters for admin user """
        
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
        """ Check removed user column for buyer user """
        
        self.__login__()
        
        # Index 2 in buyer view because missing checkboxes
        selectors = {
            "th_user": "th:nth-child(2)",
        }
        elems = get_selenium_elems(self.driver, selectors)
        
        # Validate user column is hidden
        self.assertNotEqual(elems["th_user"].text, "User")
        
    def test_no_hide_user_colum_admin(self):
        """ Check no removed user column for admin user"""
        
        self.__login_admin__()
        
        # Index 3 in buyer view because checkboxes
        selectors = {
            "th_user": "th:nth-child(3)",
        }
        elems = get_selenium_elems(self.driver, selectors)
        
        # Validate user column is hidden
        self.assertEqual(elems["th_user"].text, "User")
        
    def test_hide_sales_buyer(self):
        """ Check removed other users orders/sales """
        
        self.__login__()
        
        # Index 2 in buyer view because missing checkboxes
        selector_row = "#result_list td:nth-child(3)"
        rows = self.driver.find_elements(By.CSS_SELECTOR, selector_row)
                
        # Validate user column is hidden
        self.assertEqual(len(rows), 1)
    
    def test_no_hide_sales_admin(self):
        """ Check no removed other users orders/sales """
        
        self.__login_admin__()
        
        # Index 2 in buyer view because missing checkboxes
        selector_row = "#result_list td:nth-child(3)"
        rows = self.driver.find_elements(By.CSS_SELECTOR, selector_row)
                
        # Validate user column is hidden
        self.assertEqual(len(rows), 2)


class AdminBuyerSaleChangeTest(LiveServerTestCase):
    """ Validate buyers custom functions in sale change view """
    
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
        buyers_group = Group.objects.create(name='buyers')
        view_sale_perm = Permission.objects.get(codename='view_sale')
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
        
        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")
        
        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
        # Create sales
        set = models.Set.objects.create(
            name="set name",
            points=5,
            price=275,
            recommended=False,
            logos=5
        )
        colors_num = models.ColorsNum.objects.create(
            num=4,
            price=20,
            details="4 Colors (Trackers and 3 logo colors) +20USD"
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
        
        # go to sales change page
        link = f"{self.live_server_url}/admin/store/sale/{self.sale.id}/change/"
        self.driver.get(link)
        sleep(0.1)
        
    def __login_admin__(self):
        """ Change the user to admin and login """
        
        self.auth_user.is_superuser = True
        self.auth_user.save()
        
        self.__login__()
    
    def test_no_href_buyer(self):
        """ Validate no href attribute in links of view for buyer user """
        
        self.__login__()
        
        # Get all links
        links = self.driver.find_elements(By.TAG_NAME, "#sale_form a")
        
        # Validate all links
        for link in links:
            self.assertEqual(link.get_attribute("href"), None)
            
    def test_href_admin(self):
        """ Validate href attribute in links of view for admin user """
        
        self.__login_admin__()
        
        # Get all links
        links = self.driver.find_elements(By.TAG_NAME, "#sale_form a")
        
        # Validate all links
        for link in links:
            self.assertNotEqual(link.get_attribute("href"), None)


class SaleModelTest(TestCase):
    """ Test custom actions of sale model """
    
    def setUp(self):
        
        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com"
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
        """ Create custom id for sale """
        
        # Validate custom id
        self.assertEqual(len(self.sale.id), 12)
        
    def test_change_status_email(self):
        """ Send email to client when change status """
        
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
        """ Status change email not sent because of a excluded status """
        
        # Update sale status
        status_excluded = models.SaleStatus.objects.get(value="Reminder Sent")
        self.sale.status = status_excluded
        self.sale.save()
        
        # Validate email sent
        self.assertEqual(len(mail.outbox), 0)
        
    def test_change_status_tracking_number(self):
        """ Set status to shipped when tracking number is added """
        
        # Add tracking number
        tracking_number = "123456"
        self.sale.tracking_number = tracking_number
        self.sale.save()
        
        # Validate status
        self.assertEqual(self.sale.status.value, "Shipped")
        
    def test_send_email_tracking_number(self):
        """ Send email when tracking number changes """
        
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
        cta_link_base = f"{settings.HOST}/admin/"
        self.assertIn(cta_link_base, email_html)
        self.assertIn(tracking_number, email_html)
        
    def keep_status_no_email(self):
        """ No send email when save sale without status change """
        
        self.sale.save()
        
        # Validate email sent
        self.assertEqual(len(mail.outbox), 0)


class PromoCodeTest(TestCase):
    
    def setUp(self):
        
        # Create promo code types with a command
        call_command("apps_loaddata")
        
        # Create promo codes
        self.promo_code_amount = models.PromoCode.objects.create(
            code="sample-promo-amount",
            discount=100,
            type=models.PromoCodeType.objects.get(name="amount"),
        )
        self.promo_code_percentage = models.PromoCode.objects.create(
            code="sample-promo-percentage",
            discount=10,
            type=models.PromoCodeType.objects.get(name="percentage"),
        )
        
        self.endpoint = "/api/store/promo-code/"
        
    def test_invalid(self):
        """ Send invalid promo code and validate response """
    
        res = self.client.post(
            self.endpoint,
            data=json.dumps({"promo_code": "invalid-code"}),
            content_type="application/json"
        )
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["message"], "Invalid promo code")
        self.assertEqual(res.json()["status"], "error")
        self.assertEqual(res.json()["data"], {})
    
    def test_amount(self):
        """ Validate amount discount """
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({"promo_code": self.promo_code_amount.code}),
            content_type="application/json"
        )
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Valid promo code")
        self.assertEqual(res.json()["status"], "success")
        self.assertEqual(res.json()["data"]["value"], self.promo_code_amount.discount)
        self.assertEqual(res.json()["data"]["type"], self.promo_code_amount.type.name)
           
    def test_percentage(self):
        """ Validate percentage discount """
        
        res = self.client.post(
            self.endpoint,
            data=json.dumps({"promo_code": self.promo_code_percentage.code}),
            content_type="application/json"
        )
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Valid promo code")
        self.assertEqual(res.json()["status"], "success")
        self.assertEqual(
            res.json()["data"]["value"],
            self.promo_code_percentage.discount
        )
        self.assertEqual(
            res.json()["data"]["type"],
            self.promo_code_percentage.type.name
        )