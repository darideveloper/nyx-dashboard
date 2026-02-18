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
from django.test import LiveServerTestCase, TestCase, override_settings

import PyPDF2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from unittest.mock import patch, MagicMock

from store import models
from store.tests.payment_base import SaleViewTestMixin, SaleDoneViewTestMixin
from utils.automation import get_selenium_elems
from utils.paypal import PaypalCheckout
from utils.stripe import StripeCheckout


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


class SaleViewPaypalTest(SaleViewTestMixin, TestCase):
    """Test sale view using PayPal provider"""

    @property
    def payment_link_domain(self):
        return "paypal.com"


@override_settings(PAYMENT_PROVIDER="stripe")
class SaleViewStripeTest(SaleViewTestMixin, TestCase):
    """Test sale view using Stripe provider"""

    @property
    def payment_link_domain(self):
        return "checkout.stripe.com"

    def setUp(self):
        # Patch create
        patcher = patch("utils.stripe.stripe.checkout.Session.create")
        self.mock_create = patcher.start()

        mock_session_obj = MagicMock()
        mock_session_obj.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_session_obj.id = "cs_test_123"
        self.mock_create.return_value = mock_session_obj

        self.addCleanup(patcher.stop)

        super().setUp()


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

    def __fill_stripe_card_details__(self, number, expiry, cvc, zip_code):
        """Fill Stripe checkout card details"""

        # NOTE: Stripe uses iframes for card elements.
        # This implementation assumes we can switch to them or find inputs.
        # For simplicity, we might need to adjust based on actual DOM behavior during manual testing.

        # Example logic (needs verification against real Stripe page):
        # self.driver.switch_to.frame("stripe-card-element")
        # ...
        pass

    def __submit_stripe_payment__(self):
        """Submit Stripe payment"""
        # Click pay button
        # self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        pass

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

    @override_settings(PAYMENT_PROVIDER="stripe")
    def test_pay_stripe_sandbox_user(self):
        """Test full payment process using Stripe checkout demo/sandbox user"""

        # Open checkout page
        self.__load_checkout_page__()

        # Verify Stripe
        self.assertIn("checkout.stripe.com", self.driver.current_url)

        # Fill valid test card
        self.__fill_stripe_card_details__(
            "4242 4242 4242 4242", "12/24", "123", "12345"
        )
        self.__submit_stripe_payment__()

        # Wait for redirect
        WebDriverWait(self.driver, 20).until(
            lambda d: "sale-status=success" in d.current_url
        )

        # Validate sale done direct
        sale = models.Sale.objects.all()[0]
        redirect_page = f"?sale-id={sale.id}&sale-status=success"
        self.assertIn(redirect_page, self.driver.current_url)

        # Validate sale done status
        sale.refresh_from_db()
        self.assertEqual(sale.status.value, "Paid")


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


class SaleDonePaypalTest(SaleDoneViewTestMixin, TestCase):
    """Test sale done view using PayPal provider"""

    @property
    def commission_rate(self):
        return settings.INVOICE_PAYPAL_COMMISSION

    def get_payment_linker(self):
        return PaypalCheckout()


@override_settings(PAYMENT_PROVIDER="stripe")
class SaleDoneStripeTest(SaleDoneViewTestMixin, TestCase):
    """Test sale done view using Stripe provider"""

    @property
    def commission_rate(self):
        return settings.INVOICE_STRIPE_COMMISSION

    def get_payment_linker(self):
        return StripeCheckout()

    def setUp(self):
        # Patch create
        patcher = patch("utils.stripe.stripe.checkout.Session.create")
        self.mock_create = patcher.start()

        mock_session_obj = MagicMock()
        mock_session_obj.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_session_obj.id = "cs_test_123"
        self.mock_create.return_value = mock_session_obj

        self.addCleanup(patcher.stop)

        # Patch retrieve for is_payment_done
        patcher_retrieve = patch("utils.stripe.stripe.checkout.Session.retrieve")
        self.mock_retrieve = patcher_retrieve.start()

        mock_retrieve_session = MagicMock()
        mock_retrieve_session.payment_status = "paid"
        self.mock_retrieve.return_value = mock_retrieve_session

        self.addCleanup(patcher_retrieve.stop)

        super().setUp()

    def test_get_no_paid(self):
        """Validate sale not paid"""
        # Adjust mock to return unpaid
        self.mock_retrieve.return_value.payment_status = "unpaid"
        super().test_get_no_paid()


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
