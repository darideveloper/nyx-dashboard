import os
import json
import base64
import locale
from time import sleep

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from django.test import LiveServerTestCase, TestCase

import PyPDF2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from store import models
from utils.automation import get_selenium_elems
from utils.paypal import PaypalCheckout


class FutureStockViewTest(TestCase):

    def setUp(self):
        """Create initial data"""

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
        """Test get next future stock"""

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
        """Test when future stock is already added and
        no more future stock to add"""

        self.future_stock.added = True
        self.future_stock.save()

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

        json_data = response.json()
        self.assertEqual(json_data["next_future_stock"], 0)
        self.assertFalse(json_data["already_subscribed"])

    def test_get_email(self):
        """Test get next future stock with email endpoint"""

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
        """Test get next future stock with email endpoint,
        and user is already subscribed"""

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


class SaleViewTest(TestCase):

    def setUp(self):
        """Create initial data"""

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com", password="test_password", email="test@gmail.com"
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
                "discount": {"type": "amount", "value": 100},
            },
            "full_name": "dari",
            "country": "dev",
            "state": "street",
            "city": "ags",
            "postal_code": "20010",
            "street_address": "street 1",
            "phone": "12323123",
            "comments": "test comments",
        }

        # Files paths
        current_path = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.dirname(current_path)
        self.test_files_folder = os.path.join(app_path, "test_files")

        # Add current stock to store status
        self.current_stock = models.StoreStatus.objects.get(key="current_stock")
        self.current_stock.value = 100
        self.current_stock.save()

    def __get_logo_base64__(self, file_name: str) -> str:
        """Get logo in base64 string

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
        """Save new sale but with missing fields"""

        # Missing fields
        data = {"test": "test"}
        json_data = json.dumps(data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # First missing field detected
        self.assertEqual(res.json()["message"], "Missing field: email")

    def test_sale_no_logo(self):
        """Save new sale with full data but without logo"""

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        json_res = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_res["message"], "Sale saved")

        # Validate stripe link
        payment_link_base = "paypal.com/checkoutnow?token="
        self.assertTrue(json_res["data"]["payment_link"])
        self.assertTrue(payment_link_base in json_res["data"]["payment_link"])

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

        # Validate promo (no auto created)
        promo_data = self.data["promo"]
        promo_obj = models.PromoCode.objects.filter(code=promo_data["code"])
        self.assertEqual(promo_obj.count(), 0)

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
        self.assertEqual(sale_obj[0].promo_code, None)
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
        total = round(total, 2)
        self.assertEqual(sale_obj[0].total, total)

        # Validte empty logo
        self.assertEqual(sale_obj[0].logo, "")

    def test_logo_png(self):
        """Save sale with a logo in png"""

        image_base64 = "data:image/png;base64,"
        image_base64 += self.__get_logo_base64__("logo.png")

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate logo file
        sale = models.Sale.objects.all()[0]
        self.assertTrue(sale.logo.url)

    def test_logo_svg(self):
        """Save sale with a logo in svg"""

        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += self.__get_logo_base64__("logo.svg")

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate logo file
        sale = models.Sale.objects.all()[0]
        self.assertTrue(sale.logo.url)

    def test_logo_jpg(self):
        """Save sale with a logo in jpg
        Expect to fail because jpg is not allowed
        """

        image_base64 = "data:image/jpg;base64,"
        image_base64 += self.__get_logo_base64__("logo.jpg")

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # Validate No logo file
        sale = models.Sale.objects.all()[0]
        self.assertFalse(sale.logo)

        # Validate error response
        self.assertEqual(res.json()["status"], "error")
        self.assertEqual(res.json()["message"], "Invalid logo format")
        self.assertEqual(res.json()["data"], {})

    def test_invalid_logo(self):
        """Save sale with a logo in svg broken
        Expect to fail because svg base64 is broken
        """

        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += "invalid string"

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # Validate sale deleted
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 0)

        # Validate error response
        self.assertEqual(res.json()["status"], "error")
        self.assertEqual(res.json()["message"], "Error saving logo")
        self.assertEqual(res.json()["data"], {})

    def test_1_colors(self):
        """Save sale with single color (set color)"""

        # Change colors num to 1
        self.data["colors_num"] = 1

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
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
        """Save sale with set color and 1 logo color"""

        # Change colors num to 1
        self.data["colors_num"] = 2

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
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
        """Save sale with set color and 2 logo colors"""

        # Change colors num to 1
        self.data["colors_num"] = 3

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
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
        """Save sale with set color and 3 logo colors"""

        # Change colors num to 1
        self.data["colors_num"] = 4

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
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
        """Save new sale with a guest user"""

        # Delete old sales
        models.Sale.objects.all().delete()

        self.data["email"] = "guest_user@gmail.com"

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
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
        self.assertGreaterEqual(len(mail.outbox), 1)
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
        """Skip sale when there is no stock"""

        # Logo path
        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += self.__get_logo_base64__("logo.svg")

        # Add logo to data
        self.data["logo"] = image_base64

        # Update stock
        self.current_stock.value = "0"
        self.current_stock.save()

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)
        json_data = res.json()
        self.assertEqual(json_data["message"], "No stock available")
        self.assertEqual(json_data["status"], "error")
        self.assertEqual(json_data["data"], {})

        # Valdiate sale created
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

        # Validate sale content (logo, extras, colors, texts, etc)
        sale = sales[0]
        self.assertEqual(sale.status.value, "Pending")
        self.assertTrue(sale.logo)
        self.assertEqual(sale.addons.count(), 2)
        self.assertEqual(sale.set.name, self.data["set"])
        self.assertEqual(sale.colors_num.num, self.data["colors_num"])
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3.name, self.data["logo_color_3"])
        self.assertEqual(sale.full_name, self.data["full_name"])
        self.assertEqual(sale.country, self.data["country"])
        self.assertEqual(sale.state, self.data["state"])
        self.assertEqual(sale.city, self.data["city"])
        self.assertEqual(sale.postal_code, self.data["postal_code"])
        self.assertEqual(sale.street_address, self.data["street_address"])
        self.assertEqual(sale.phone, self.data["phone"])
        self.assertEqual(sale.comments, self.data["comments"])

    def test_no_comments(self):
        """Save sale without comments"""

        # Remove comments
        self.data.pop("comments")

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Valdiate sale created
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.comments, "")

    def test_long_comments(self):
        """Save sale without comments"""

        # Remove comments
        self.data["comments"] = "a" * 5000

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Valdiate sale created
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.comments, self.data["comments"])

    def test_pending_sale(self):
        """Try to create new sale when user has a pending sale
        Expect to delete old sale, create new one and send emails
        """

        # Create pending sale
        status = models.SaleStatus.objects.get(value="Pending")
        pending_sale = models.Sale.objects.create(
            user=self.auth_user,
            set=models.Set.objects.all().first(),
            colors_num=models.ColorsNum.objects.all().first(),
            color_set=models.Color.objects.all().first(),
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
        pending_sale_id = pending_sale.id

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate unique sale for the user
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

        # Validate sale created
        sale = sales[0]
        self.assertEqual(sale.status.value, "Pending")

        # Validate 2 emails sent
        self.assertEqual(len(mail.outbox), 2)

        # Validate user email text content
        subject = "Nyx Trackers Sale Updated"
        cta_link = f"{settings.HOST}/sign-up"
        cta_text = "Sign up"
        sent_email = mail.outbox[0]
        send_email_html = sent_email.alternatives[0][0]
        self.assertEqual(sent_email.subject, subject)
        self.assertIn(cta_link, send_email_html)
        self.assertIn(cta_text, send_email_html)

        # Validate admin email
        subject = "Nyx Trackers Sale Updated by User"
        cta_link = f"{settings.HOST}/admin/store/sale/"
        cta_link += "?user__id__exact="
        cta_text = "View sale in dashboard"
        cta_text = "View sale in dashboard"
        sent_email = mail.outbox[1]
        send_email_html = sent_email.alternatives[0][0]
        self.assertEqual(sent_email.subject, subject)
        self.assertIn(cta_link, send_email_html)
        self.assertIn(cta_text, send_email_html)

        # Validate new sale id
        self.assertNotEqual(sale.id, pending_sale_id)

    def test_pending_sale_no_stock(self):
        """Try to create new sale when user has a pending sale and there
        is no stock.
        Expect to delete old sale, create new one and send emails
        """

        # Update stock in system
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock.value = 0
        current_stock.save()

        # Create pending sale
        status = models.SaleStatus.objects.get(value="Pending")
        pending_sale = models.Sale.objects.create(
            user=self.auth_user,
            set=models.Set.objects.all().first(),
            colors_num=models.ColorsNum.objects.all().first(),
            color_set=models.Color.objects.all().first(),
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
        pending_sale_id = pending_sale.id

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # Validate unique sale for the user
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

        # Validate sale created
        sale = sales[0]
        self.assertEqual(sale.status.value, "Pending")

        # Validate new sale id
        self.assertNotEqual(sale.id, pending_sale_id)

    def test_many_pending_sale(self):
        """Try to create new sale when user has a many pending sales
        Expect to delete old sales, create a new one
        """

        # Create pending sale
        status = models.SaleStatus.objects.get(value="Pending")
        for _ in range(3):
            models.Sale.objects.create(
                user=self.auth_user,
                set=models.Set.objects.all().first(),
                colors_num=models.ColorsNum.objects.all().first(),
                color_set=models.Color.objects.all().first(),
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

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate unique sale for the user
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

    def test_no_promo_code(self):

        # Delete default promo codes
        models.PromoCode.objects.all().delete()

        # Send data
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate total
        total = 0
        colors_num_obj = models.ColorsNum.objects.get(id=self.data["colors_num"])
        set_obj = models.Set.objects.get(name=self.data["set"])
        total += colors_num_obj.price
        total += set_obj.price
        extras = models.Addon.objects.filter(name__in=self.data["included_extras"])
        extras_total = sum([extra.price for extra in extras])
        total += extras_total

        # Validate total and promo code
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.promo_code, None)
        self.assertEqual(sale.total, total)

    def test_promo_code_amount(self):

        # Delete default promo codes
        models.PromoCode.objects.all().delete()

        # Create promo code
        promo_code = models.PromoCode.objects.create(
            code="test-promo",
            discount=100,
            type=models.PromoCodeType.objects.get(name="amount"),
        )

        # Add promo code to data
        self.data["promo"]["code"] = promo_code.code
        self.data["promo"]["discount"] = {
            "type": promo_code.type.name,
            "value": promo_code.discount,
        }

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate total
        total = 0
        colors_num_obj = models.ColorsNum.objects.get(id=self.data["colors_num"])
        set_obj = models.Set.objects.get(name=self.data["set"])
        total += colors_num_obj.price
        total += set_obj.price
        extras = models.Addon.objects.filter(name__in=self.data["included_extras"])
        extras_total = sum([extra.price for extra in extras])
        total += extras_total

        # Validate total and promo code
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.promo_code, promo_code)
        self.assertEqual(sale.total, total - promo_code.discount)

    def test_promo_code_percentage(self):

        # Delete default promo codes
        models.PromoCode.objects.all().delete()

        # Create promo code
        promo_code = models.PromoCode.objects.create(
            code="test-promo",
            discount=10,
            type=models.PromoCodeType.objects.get(name="percentage"),
        )

        # Add promo code to data
        self.data["promo"]["code"] = promo_code.code
        self.data["promo"]["discount"] = {
            "type": promo_code.type.name,
            "value": promo_code.discount,
        }

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate total
        total = 0
        colors_num_obj = models.ColorsNum.objects.get(id=self.data["colors_num"])
        set_obj = models.Set.objects.get(name=self.data["set"])
        total += colors_num_obj.price
        total += set_obj.price
        extras = models.Addon.objects.filter(name__in=self.data["included_extras"])
        extras_total = sum([extra.price for extra in extras])
        total += extras_total

        # Validate total and promo code
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.promo_code, promo_code)
        self.assertEqual(sale.total, total * (1 - promo_code.discount / 100))


class SaleViewTestLive(LiveServerTestCase):
    """Test sales view in chrome (for external resources and validations)"""

    host = "localhost"
    port = 8000

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

        # Create initial data
        self.endpoint = "/api/store/sale/"
        call_command("apps_loaddata")

        # Add current stock to store status
        self.current_stock = models.StoreStatus.objects.get(key="current_stock")
        self.current_stock.value = 100
        self.current_stock.save()

        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Initial data
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
                "discount": {"type": "amount", "value": 100},
            },
            "full_name": "dari",
            "country": "dev",
            "state": "street",
            "city": "ags",
            "postal_code": "20010",
            "street_address": "street 1",
            "phone": "12323123",
            "comments": "test comments",
        }

        self.selectors = {
            "amount": "header button > span",
            "login_btn": "p + button",
            "input_email": "#email",
            "next_btn": "button",
            "input_pass": "#password",
            "submit_btn": "#btnLogin",
            "pay_btn": '[data-id="payment-submit-btn"]',
        }

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def __load_checkout_page__(self) -> str:
        """Get checkout payment link submiting sale and and open it

        Returns:
            str: Payment checkout link
        """

        res = self.client.post(
            self.endpoint, data=json.dumps(self.data), content_type="application/json"
        )

        # Validate response
        json_res = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_res["message"], "Sale saved")

        # Open checkout page
        payment_link = json_res["data"]["payment_link"]
        self.driver.get(payment_link)
        sleep(3)

    def __click__(self, selector: str):
        """Click on element in checkout page

        Args:
            selector (str): css selector to click on
        """

        element = self.driver.find_element(By.CSS_SELECTOR, selector)
        element.click()
        sleep(1)

    def __send_text__(self, selector: str, text: str):
        """Send text to element in checkout page

        Args:
            selector (str): css selector to send text to
            text (str): Text to send
        """

        element = self.driver.find_element(By.CSS_SELECTOR, selector)
        element.send_keys(text)
        sleep(3)

    def test_checkout_total(self):
        """Test generate sale with no promo code and valdiate amount in checkout"""

        self.__load_checkout_page__()

        # Validate amount
        amount = self.driver.find_element(
            By.CSS_SELECTOR, self.selectors["amount"]
        ).text.replace("$", "")
        sale = models.Sale.objects.all()[0]
        self.assertEqual(float(amount), sale.total)

    def test_checkout_promo_code(self):
        """Test generate sale with a promo code and valdiate amount in checkout"""

        # Create promo code
        models.PromoCode.objects.create(
            code="sample-promo",
            discount=100,
            type=models.PromoCodeType.objects.get(name="amount"),
        )

        # Open checkout page
        self.__load_checkout_page__()

        # Validate amount
        amount = self.driver.find_element(
            By.CSS_SELECTOR, self.selectors["amount"]
        ).text.replace("$", "")
        sale = models.Sale.objects.all()[0]
        self.assertEqual(float(amount), sale.total)
        self.assertEqual(float(amount), 234.0)

    def test_pay_sandbox_user(self):
        """Test full payment process using the checkout demo/sandbox user"""

        # Open checkout page
        self.__load_checkout_page__()

        # Open login page
        self.__click__(self.selectors["login_btn"])

        # Type email
        self.__send_text__(self.selectors["input_email"], settings.PAYPAL_SANDBOX_USER)
        self.__click__(self.selectors["next_btn"])

        # Type password
        self.__send_text__(
            self.selectors["input_pass"], settings.PAYPAL_SANDBOX_PASSWORD
        )
        self.__click__(self.selectors["submit_btn"])
        sleep(3)

        # Click pay button
        self.__click__(self.selectors["pay_btn"])
        sleep(4)

        # Validate sale done direct
        sale = models.Sale.objects.all()[0]
        redirect_page = f"?sale-id={sale.id}&sale-status=success"
        self.assertIn(redirect_page, self.driver.current_url)

        # Validate sale done status
        sale.refresh_from_db()
        self.assertEqual(sale.status.value, "Paid")

        # Validate payment link updated
        self.assertIn(
            "https://www.paypal.com/unifiedtransactions/details/payment/",
            sale.payment_link,
        )


class CurrentStockViewTest(TestCase):

    def setUp(self):
        """Create initial data"""

        # Create initial data
        call_command("apps_loaddata")

        self.current_stock = models.StoreStatus.objects.get(
            key="current_stock",
        )
        self.current_stock.value = 100
        self.current_stock.save()

        self.endpoint = "/api/store/current-stock/"

    def test_get(self):
        """Get current stock"""

        res = self.client.get(self.endpoint)

        # Validate response
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["message"], "Current stock")
        self.assertEqual(json_data["data"]["current_stock"], 100)

    def test_get_0(self):
        """Get current stock with 0 value"""

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

    def test_missing_current_stock_key(self):
        """Try to get current stock without the key
        Expected to create the key with default value
        """

        # Delete current stock
        self.current_stock.delete()

        res = self.client.get(self.endpoint)

        # Validate response
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(json_data["status"], "success")
        self.assertEqual(json_data["message"], "Current stock")
        self.assertEqual(json_data["data"]["current_stock"], 0)

        # Validate stock created
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        self.assertEqual(int(current_stock.value), 0)


class SaleDoneViewTest(TestCase):

    def setUp(self):
        """Create initial data"""

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com",
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
        app_path = os.path.dirname(current_path)
        test_files_folder = os.path.join(app_path, "test_files")

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
            total=510,
            status=status,
        )

        # Add logo to sale
        logo = SimpleUploadedFile(
            name="logo.png",
            content=open(logo_path, "rb").read(),
            content_type="image/png",
        )
        self.sale.logo = logo
        self.sale.save()

        # Request data
        self.endpoint = "/api/store/sale-done"

        # Set current stock to 100
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock.value = 100
        current_stock.save()

        invoice_num = models.StoreStatus.objects.get(key="invoice_num")
        invoice_num.value = 200
        invoice_num.save()

        self.redirect_page = settings.LANDING_HOST

        # Connect paypal
        self.paypal_checkout = PaypalCheckout()

        # Add payment link to sale
        payment_link = self.paypal_checkout.get_checkout_link(
            sale_id=self.sale.id,
            title="Nyx Trackers Test Sale",
            price=self.sale.total,
            description="Test sale description",
        )
        self.sale.payment_link = payment_link["self"]
        self.sale.save()

    def test_get(self):
        """Validate sale already paid"""

        # Validate sale and force payment validation
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")

        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={self.sale.id}&sale-status=success"
        self.assertEqual(res.url, self.redirect_page)

        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Paid")

    def test_get_no_paid(self):
        """Validate sale not paid"""

        # Validate sale (no force)
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")

        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={self.sale.id}&sale-status=error"
        self.assertEqual(res.url, self.redirect_page)

        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Pending")

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
        """Validate email sent content after sale confirmation"""

        # Validate redirect
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")
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
        cta_link_base = f"{settings.HOST}/admin/store/sale/{self.sale.id}/change/"
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
        """Validate email sent without logo"""

        # Remove logo from sale
        self.sale.logo = None
        self.sale.save()

        # Validate redirect
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")
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

    def test_invalid_payment_email(self):
        """Validate email sent to client when payment is invalid"""

        # No force test sale (detect invalid payment)
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")
        self.assertEqual(res.status_code, 302)

        # Validate email sent
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Nyx Trackers Payment Error")
        self.assertEqual(email.to, [self.sale.user.email])
        self.assertIn("There was an error with your payment.", email.body)
        self.assertIn("Your order has not been processed.", email.body)
        self.assertIn("Please try again or contact us for support.", email.body)

    def test_invalid_payment_no_email_status(self):
        """No send status change email when order its invalid"""

        payment_error_status = models.SaleStatus.objects.get(value="Payment Error")
        self.sale.status = payment_error_status
        self.sale.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_invoice_created(self):
        """Validate sale already paid and invoice created"""

        # Get initial invoice_num
        invoice_num = models.StoreStatus.objects.get(key="invoice_num")
        self.assertEqual(int(invoice_num.value), 200)

        # Validate sale and force payment validation
        self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")

        # Validate invoice field no empty
        self.sale.refresh_from_db()
        self.assertNotEqual(self.sale.invoice_file.name, "")
        self.assertTrue(self.sale.invoice_file.name.endswith(".pdf"))

        # Validate store status updated
        invoice_num.refresh_from_db()
        self.assertEqual(int(invoice_num.value), 201)

    def test_invoice_no_created(self):
        """Validate sale not paid and no invoice created"""

        # Validate sale (no force)
        self.client.get(f"{self.endpoint}/{self.sale.id}/")

        # Validate no paid status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Pending")

        # Validate invoice field empty
        self.assertEqual(self.sale.invoice_file.name, "")

        # Validate store status not updated
        invoice_num = models.StoreStatus.objects.get(key="invoice_num")
        self.assertEqual(int(invoice_num.value), 200)

    def test_invoice_content(self):
        """Validate invoice content"""

        # Update invoice amounts to easy calcs
        self.sale.total = 100
        self.sale.save()

        # Validate sale and force payment validation
        self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")

        # Validate invoice file exists
        self.sale.refresh_from_db()
        self.assertIsNotNone(self.sale.invoice_file)

        # Get incoide file
        pdf_text = ""
        with self.sale.invoice_file.open("rb") as invoice_file:
            reader = PyPDF2.PdfReader(invoice_file)
            pdf_text = reader.pages[0].extract_text()

        # Update locale for date formatting
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

        # Get current invoice_num
        invoice_num_str = models.StoreStatus.objects.get(key="invoice_num").value

        # get and formatd data
        date = timezone.now().strftime("%d de %B de %Y")
        invoice_num = int(invoice_num_str) - 1
        name = self.sale.user.get_full_name()
        city = self.sale.city
        state = self.sale.state
        street = self.sale.street_address
        pc = self.sale.postal_code
        country = self.sale.country
        phone = self.sale.phone
        email = self.sale.user.email
        quantity = 1
        total = self.sale.total
        igi = total * settings.INVOICE_IGI_COMMISSION / 100
        paypal = total * settings.INVOICE_PAYPAL_COMMISSION / 100
        base = total - igi - paypal
        total_str = f"{total:.2f}USD"
        igi_str = f"{igi:.2f}USD"
        paypal_str = f"{paypal:.2f}USD"
        base_str = f"{base:.2f}USD"

        # Validate data in PDF
        self.assertIn(date, pdf_text)
        self.assertIn(str(invoice_num), pdf_text)
        self.assertIn(name, pdf_text)
        self.assertIn(city, pdf_text)
        self.assertIn(state, pdf_text)
        self.assertIn(street, pdf_text)
        self.assertIn(pc, pdf_text)
        self.assertIn(country, pdf_text)
        self.assertIn(phone, pdf_text)
        self.assertIn(email, pdf_text)
        self.assertIn(str(quantity), pdf_text)
        self.assertIn(total_str, pdf_text)
        self.assertIn(igi_str, pdf_text)
        self.assertIn(paypal_str, pdf_text)
        self.assertIn(base_str, pdf_text)


class PromoCodeViewTest(TestCase):

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
        """Send invalid promo code and validate response"""

        res = self.client.post(
            self.endpoint,
            data=json.dumps({"promo_code": "invalid-code"}),
            content_type="application/json",
        )

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["message"], "Invalid promo code")
        self.assertEqual(res.json()["status"], "error")
        self.assertEqual(res.json()["data"], {})

    def test_amount(self):
        """Validate amount discount"""

        res = self.client.post(
            self.endpoint,
            data=json.dumps({"promo_code": self.promo_code_amount.code}),
            content_type="application/json",
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Valid promo code")
        self.assertEqual(res.json()["status"], "success")
        self.assertEqual(res.json()["data"]["value"], self.promo_code_amount.discount)
        self.assertEqual(res.json()["data"]["type"], self.promo_code_amount.type.name)

    def test_percentage(self):
        """Validate percentage discount"""

        res = self.client.post(
            self.endpoint,
            data=json.dumps({"promo_code": self.promo_code_percentage.code}),
            content_type="application/json",
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Valid promo code")
        self.assertEqual(res.json()["status"], "success")
        self.assertEqual(
            res.json()["data"]["value"], self.promo_code_percentage.discount
        )
        self.assertEqual(
            res.json()["data"]["type"], self.promo_code_percentage.type.name
        )


class PendingOderViewTest(TestCase):

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

        self.endpoint = "/api/store/pending-order/"

    def test_(self):
        """Validate True response when user has pending orders"""

        # Submit request
        response = self.client.post(
            self.endpoint,
            data=json.dumps({"email": self.auth_user.email}),
            content_type="application/json",
        )

        # Validte response status
        self.assertEqual(response.status_code, 200)

        # Validate response content
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Pending orders status")
        self.assertEqual(data["data"]["has_pending_order"], True)

    def test_no_pending_ode(self):
        """Validate False response when user has no pending orders"""

        # Dalete order
        self.sale.delete()

        # Submit request
        response = self.client.post(
            self.endpoint,
            data=json.dumps({"email": self.auth_user.email}),
            content_type="application/json",
        )

        # Validte response status
        self.assertEqual(response.status_code, 200)

        # Validate response content
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Pending orders status")
        self.assertEqual(data["data"]["has_pending_order"], False)

    def test_user_not_found(self):
        """Validate False response when user is not found"""

        # Dalete user
        self.auth_user.delete()
        email = self.auth_user.email

        # Submit request
        response = self.client.post(
            self.endpoint,
            data=json.dumps({"email": email}),
            content_type="application/json",
        )

        # Validte response status
        self.assertEqual(response.status_code, 200)

        # Validate response content
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Pending orders status")
        self.assertEqual(data["data"]["has_pending_order"], False)


class PaymentLinkView(LiveServerTestCase):

    def setUp(self):
        """Create initial data"""

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com",
        )

        # Create initial data
        call_command("apps_loaddata")

        # Create sale
        set = models.Set.objects.all().first()

        colors_num = models.ColorsNum.objects.all().first()

        color = models.Color.objects.all().first()
        status = models.SaleStatus.objects.get(value="Pending")

        # Files paths
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(app_path, "test_files", "logo.png")

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
            total=510,
            status=status,
        )

        # Add logo to sale
        logo = SimpleUploadedFile(
            name="logo.png",
            content=open(logo_path, "rb").read(),
            content_type="image/png",
        )
        self.sale.logo = logo
        self.sale.save()

        # Request data
        self.endpoint = f"/api/store/payment-link/{self.sale.id}/"

        # Set current stock to 100
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock.value = 100
        current_stock.save()

        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Css selectors
        self.selectors = {
            "amount": "header button > span",
        }

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    def test_get_valid_sale(self):
        """Test get valid payment link and redirect to paypal"""

        # Open link
        self.driver.get(self.live_server_url + self.endpoint)
        sleep(2)

        # Validate paypal link
        self.assertIn("paypal.com", self.driver.current_url)
        self.assertIn("checkoutnow", self.driver.current_url)
        self.assertIn("token", self.driver.current_url)

        # Validate sale data in paypal
        elems = get_selenium_elems(self.driver, self.selectors)
        amount = elems["amount"].text
        amount_clean = float(amount.replace("$", ""))
        self.assertEqual(amount_clean, self.sale.total)

    def test_invalid_sale(self):
        """Test get invalid payment link and redirect error landing page"""

        # Delete sale
        self.sale.delete()

        # Open link
        self.driver.get(self.live_server_url + self.endpoint)
        sleep(2)

        # Validate 404 page
        self.assertIn("sale-id", self.driver.current_url)
        self.assertIn("sale-status=error", self.driver.current_url)
