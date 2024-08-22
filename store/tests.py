import os
import json
import base64
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


class SaleTestCase(TestCase):

    def setUp(self):
        """ Create initial data """

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com"
        )

        self.endpoint = "/api/store/sale/"
        
        # Initial data
        self.data = {
            "email": self.auth_user.email,
            "set": {
                "name": "set name",
                "points": 5,
                "price": 275,
                "recommended": False,
                "logos": 5
            },
            "colors_num": {
                "num": 4,
                "price": 20,
                "details": "4 Colors (Trackers and 3 logo colors) +20USD"
            },
            "set_color": "blue",
            "logo_color_1": "white",
            "logo_color_2": "red",
            "logo_color_3": "blue",
            "logo": "",
            "included_extras": [
                {
                    "name": "extra 1",
                    "price": 14,
                    "exclude_sets": []
                },
                {
                    "name": "extra 2",
                    "price": 25,
                    "exclude_sets": []
                }
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
        self.current_stock = models.StoreStatus.objects.create(
            key="current_stock",
            value="100",
        )

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

        # Validate sale status
        status = models.SaleStatus.objects.all()
        self.assertEqual(status.count(), 1)
        self.assertEqual(status[0].value, "Pending")

        # Validate set
        set_data = self.data["set"]
        set_obj = models.Set.objects.filter(name=set_data["name"])
        self.assertEqual(set_obj.count(), 1)
        self.assertEqual(set_obj[0].points, set_data["points"])
        self.assertEqual(set_obj[0].price, set_data["price"])
        self.assertEqual(set_obj[0].recommended, set_data["recommended"])
        self.assertEqual(set_obj[0].logos, set_data["logos"])

        # Validate colors num
        colors_num_data = self.data["colors_num"]
        colors_num_obj = models.ColorsNum.objects.filter(
            num=colors_num_data["num"])
        self.assertEqual(colors_num_obj.count(), 1)
        self.assertEqual(colors_num_obj[0].price, colors_num_data["price"])
        self.assertEqual(colors_num_obj[0].details, colors_num_data["details"])

        # Validate addons
        addons_data = self.data["included_extras"]
        addons_objs = []
        for addon_data in addons_data:
            addon_obj = models.Addon.objects.filter(name=addon_data["name"])
            self.assertEqual(addon_obj.count(), 1)
            self.assertEqual(addon_obj[0].price, addon_data["price"])
            addons_objs.append(addon_obj[0])

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
        self.assertEqual(sale_obj[0].set, set_obj[0])
        self.assertEqual(sale_obj[0].colors_num, colors_num_obj[0])
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
        self.assertEqual(sale_obj[0].status, status[0])

        # Validate total
        total = 0
        total += set_obj[0].price
        total += colors_num_obj[0].price
        for addon_obj in addons_objs:
            total += addon_obj.price
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
        self.assertTrue(sale.logo.path)
        
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
        self.assertTrue(sale.logo.path)

    def test_1_colors(self):
        """ Save sale with single color (set color) """
        
        # Change colors num to 1
        self.data["colors_num"]["num"] = 1
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate colors num created
        colors_num = models.ColorsNum.objects.all()[0]
        self.assertEqual(colors_num.num, 1)
                
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1, None)
        self.assertEqual(sale.logo_color_2, None)
        self.assertEqual(sale.logo_color_3, None)
        
    def test_2_color(self):
        """ Save sale with set color and 1 logo color """
        
        # Change colors num to 1
        self.data["colors_num"]["num"] = 2
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate colors num created
        colors_num = models.ColorsNum.objects.all()[0]
        self.assertEqual(colors_num.num, 2)
                
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2, None)
        self.assertEqual(sale.logo_color_3, None)
        
    def test_3_color(self):
        """ Save sale with set color and 2 logo colors """
        
        # Change colors num to 1
        self.data["colors_num"]["num"] = 3
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate colors num created
        colors_num = models.ColorsNum.objects.all()[0]
        self.assertEqual(colors_num.num, 3)
                
        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3, None)
        
    def test_4_color(self):
        """ Save sale with set color and 3 logo colors """
        
        # Change colors num to 1
        self.data["colors_num"]["num"] = 4
        
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint,
            data=json_data,
            content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        
        # Validate colors num created
        colors_num = models.ColorsNum.objects.all()[0]
        self.assertEqual(colors_num.num, 4)
                
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
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.username, self.data["email"])
        self.assertEqual(user.email, self.data["email"])
        
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
        
        
class CurrentStockTestCase(TestCase):

    def setUp(self):
        """ Create initial data """
        
        self.current_stock = models.StoreStatus.objects.create(
            key="current_stock",
            value="100",
        )
        
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