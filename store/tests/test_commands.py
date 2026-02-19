import json
from time import sleep

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, LiveServerTestCase, override_settings
from django.utils import timezone

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from store import models


class FutureStockUpdateTest(TestCase):
    def setUp(self):
        # Create initial status
        self.current_stock = models.StoreStatus.objects.create(
            key="current_stock", value="0"
        )

        # Create future stocks
        self.future_stock = models.FutureStock.objects.create(
            amount=5, datetime=timezone.now() - timezone.timedelta(days=1), added=False
        )

        # Create subscriptions
        self.user_name = "test@email.com"
        self.user = models.User.objects.create_user(
            username=self.user_name,
            email=self.user_name,
            password="test1234",
            is_active=True,
            is_staff=False,
        )
        self.subscription = models.FutureStockSubscription.objects.create(
            future_stock=self.future_stock, user=self.user
        )

        self.cron_name = "future_stock_update"

    def test_datetime_reached(self):
        """Test add stock when future stock datetime is reached"""

        # Freeze time to ensure consistent test results
        call_command(self.cron_name)

        # Check if the future stock was updated
        self.future_stock.refresh_from_db()
        self.assertTrue(self.future_stock.added)

        # Check if the current stock was updated
        self.current_stock.refresh_from_db()
        self.assertEqual(int(self.current_stock.value), 5)

        # Validate emails sent
        self.assertEqual(len(mail.outbox), 1)

        # Validate email text content
        subject = "New sets available now!"
        cta_link_base = f"{settings.LANDING_HOST}#buy-form"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        self.assertIn(self.user.first_name, sent_email.body)
        self.assertIn(self.user.last_name, sent_email.body)

        # Validate email html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)

    def test_datetime_reached_inactive_subscription(self):
        """Test add stock when future stock datetime is reached
        but subscription is inactive"""

        # Deactivate subscription
        self.subscription.active = False
        self.subscription.save()

        # Freeze time to ensure consistent test results
        call_command(self.cron_name)

        # Check if the future stock was updated
        self.future_stock.refresh_from_db()
        self.assertTrue(self.future_stock.added)

        # Check if the current stock was updated
        self.current_stock.refresh_from_db()
        self.assertEqual(int(self.current_stock.value), 5)

        # Validate emails sent
        self.assertEqual(len(mail.outbox), 0)

    def test_datetime_reached_new_user(self):
        """Test add stock when future stock datetime is reached
        but the user its new (from landing)"""

        # Delete original user
        self.user.delete()

        user_email = "new@test.com"
        res = self.client.post(
            "/api/store/future-stock-subscription/",
            data=json.dumps(
                {
                    "email": user_email,
                    "type": "add",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)

        # Freeze time to ensure consistent test results
        call_command(self.cron_name)

        # Check if the future stock was updated
        self.future_stock.refresh_from_db()
        self.assertTrue(self.future_stock.added)

        # Check if the current stock was updated
        self.current_stock.refresh_from_db()
        self.assertEqual(int(self.current_stock.value), 5)

        # Validate emails sent
        self.assertEqual(len(mail.outbox), 1)

        # Vsalite email address
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, [user_email])

        # Validate email text content
        subject = "New sets available now!"
        cta_link_base = f"{settings.LANDING_HOST}#buy-form"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)
        self.assertIn(self.user.first_name, sent_email.body)
        self.assertIn(self.user.last_name, sent_email.body)

        # Validate email html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)

    def test_datetime_not_reached(self):
        """Test add stock when future stock datetime is not reached"""

        # Update the datetime to the future
        self.future_stock.datetime = timezone.now() + timezone.timedelta(days=1)
        self.future_stock.save()

        # Freeze time to ensure consistent test results
        call_command(self.cron_name)

        # Check if the future stock was not updated
        self.future_stock.refresh_from_db()
        self.assertFalse(self.future_stock.added)

        # Check if the current stock was not updated
        self.current_stock.refresh_from_db()
        self.assertEqual(int(self.current_stock.value), 0)


class PaymentReminderBaseTest(TestCase):
    """Base class with reusable methods for PaymentReminder command"""

    def setUp(self):
        """Create initial data for tests"""

        # Default email data
        self.email_data = {
            "subject": "Don't forget to pay for your order!",
            "cta_text": "Pay now",
            "cta_link": "/api/store/payment-link/",
            "texts": [
                "You have an order pending payment.",
                "You are one step away from getting your dream Fbt!"
                " Click here to finish the process.",
            ],
        }

    def __create_sale__(self, status_str: str):
        """Create new sale with spaecified status

        Args:
            status_str (str): Sale status value
        """

        # Load data with command
        call_command("apps_loaddata")

        # Create sale
        set = models.Set.objects.first()
        colors_num = models.ColorsNum.objects.first()
        color = models.Color.objects.first()
        status = models.SaleStatus.objects.get(value=status_str)

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
        )

    def __validate_email__(
        self, email_index: int = 0, is_promo: bool = False, sale_id: int = None
    ):
        """Validate email content

        Args:
            email_index (int): Index of the email in the outbox
            is_promo (bool): Check if the email is a promo email
        """

        if is_promo:
            self.email_data["subject"] += " - 15% discount"
            self.email_data["cta_text"] += " with 15% discount"
            self.email_data["texts"].append(
                "Just for you, we are offering a 15%" " discount on your order."
            )

        # Validate email main data
        sent_email = mail.outbox[email_index]
        self.assertEqual(sent_email.subject, self.email_data["subject"])
        self.assertIn(self.email_data["cta_text"], sent_email.body)
        self.assertIn(self.email_data["cta_link"] + sale_id, sent_email.body)
        for text in self.email_data["texts"]:
            self.assertIn(text, sent_email.body)


class PaymentReminderTest(PaymentReminderBaseTest):
    """Test payment reminder command"""

    def setUp(self):

        super().setUp()

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com", password="test_password", email="test@gmail.com"
        )

        self.__create_sale__("Pending")

        self.cron_name = "payment_reminder"

        # Create data with command
        call_command("apps_loaddata")

    def test_send_remainder(self):
        """Send remainder email and validate content"""

        call_command(self.cron_name)

        # Validte single email sent
        self.assertEqual(len(mail.outbox), 1)

        # Validate sale info
        sale = models.Sale.objects.first()
        self.assertEqual(sale.status.value, "Reminder Sent")
        self.assertEqual(sale.reminders_sent, 1)

        # Validate email content
        self.__validate_email__(sale_id=sale.id)

    def test_send_multiple_remainders(self):
        """Send 2 remainder emails"""

        # Create new sale
        self.__create_sale__("Pending")

        call_command(self.cron_name)

        # Validte 2 emails sent
        self.assertEqual(len(mail.outbox), 2)

        # Validate sale status updated
        sales = models.Sale.objects.all()
        for sale in sales:
            self.assertEqual(sale.status.value, "Reminder Sent")
            self.assertEqual(sale.reminders_sent, 1)

    def test_no_sales(self):
        """No send remainder where there are no sales pending"""

        # Create sale in "Paid" status
        models.Sale.objects.all().delete()
        self.__create_sale__("Paid")

        call_command(self.cron_name)

        # Validte no emails sent
        self.assertEqual(len(mail.outbox), 0)

        # Validate sale status
        sale = models.Sale.objects.first()
        self.assertEqual(sale.status.value, "Paid")
        self.assertEqual(sale.reminders_sent, 0)

    def test_sale_already_sent(self):
        """No send remainder when 3 reminders have been sent"""

        # Create sale in "Reminder Sent" status
        models.Sale.objects.all().delete()
        self.__create_sale__("Reminder Sent")
        sale = models.Sale.objects.first()
        sale.reminders_sent = 3
        sale.save()

        call_command(self.cron_name)

        # Validte no emails sent
        self.assertEqual(len(mail.outbox), 0)

        # Validate sale status
        sale.refresh_from_db()
        self.assertEqual(sale.status.value, "Reminder Sent")
        self.assertEqual(sale.reminders_sent, 3)

    def test_send_discount(self):
        """Send discount on 3rd remainder"""

        # Create sale in "Reminder Sent" status
        models.Sale.objects.all().delete()
        self.__create_sale__("Reminder Sent")
        sale = models.Sale.objects.first()
        sale.reminders_sent = 2
        sale.save()

        call_command(self.cron_name)

        # Validte email sent
        self.assertEqual(len(mail.outbox), 1)

        # Validate sale status
        sale.refresh_from_db()
        self.assertEqual(sale.status.value, "Reminder Sent")
        self.assertEqual(sale.reminders_sent, 3)

        # Validate email content
        self.__validate_email__(is_promo=True, sale_id=sale.id)


class PaymentReminderTestLive(PaymentReminderBaseTest, LiveServerTestCase):
    """Test sales view in chrome (for external resources and validations)"""

    def setUp(self):

        super().setUp()

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

        # Save cron name
        self.cron_name = "payment_reminder"

        # Create data
        self.__create_sale__("Pending")
        call_command("apps_loaddata")

        # Configure selenium
        chrome_options = Options()
        if settings.TEST_HEADLESS:
            chrome_options.add_argument("--headless")

        # Start selenium
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Global selectors
        self.selectors = {
            "email_cta": ".btn-primary a",
            "checkout_amount": "header button > span",
        }

    def tearDown(self):
        """Close selenium"""
        try:
            self.driver.quit()
        except Exception:
            pass

    @override_settings(PAYMENT_PROVIDER="paypal")
    def test_remainder_checkout_amount_paypal(self):
        """Send remainder email and validate checkout amount"""

        call_command(self.cron_name)

        # Validate sale info
        sale = models.Sale.objects.first()
        self.assertEqual(sale.reminders_sent, 1)

        # Get checkout link from email
        email_content = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(email_content, "html.parser")
        cta_link = soup.select_one(self.selectors["email_cta"])["href"]

        # Replace host wiuth test host in cta link
        cta_link = cta_link.replace(settings.HOST, self.live_server_url)

        # Open checkout link in selenium
        self.driver.get(cta_link)
        sleep(3)

        # Validate amount
        amount = self.driver.find_element(
            By.CSS_SELECTOR, self.selectors["checkout_amount"]
        ).text.replace("$", "")
        sale = models.Sale.objects.all()[0]
        self.assertEqual(float(amount), sale.total)

    @override_settings(PAYMENT_PROVIDER="stripe")
    def test_remainder_checkout_amount_stripe(self):
        """Send remainder email and validate checkout amount"""

        # Update css selectors
        self.selectors["checkout_amount"] = 'img[alt="US"] + span.CurrencyAmount'

        call_command(self.cron_name)

        # Validate sale info
        sale = models.Sale.objects.first()
        self.assertEqual(sale.reminders_sent, 1)

        # Get checkout link from email
        email_content = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(email_content, "html.parser")
        cta_link = soup.select_one(self.selectors["email_cta"])["href"]

        # Replace host wiuth test host in cta link
        cta_link = cta_link.replace(settings.HOST, self.live_server_url)

        # Open checkout link in selenium
        self.driver.get(cta_link)
        sleep(3)

        # Validate amount
        amount = self.driver.find_element(
            By.CSS_SELECTOR, self.selectors["checkout_amount"]
        ).text.replace("$", "")
        sale = models.Sale.objects.all()[0]
        self.assertEqual(float(amount), sale.total)

    @override_settings(PAYMENT_PROVIDER="paypal")
    def test_remainder_checkout_amount_discount_paypal(self):
        """Send discount on 3rd remainder"""

        # Create sale in "Reminder Sent" status
        models.Sale.objects.all().delete()
        self.__create_sale__("Reminder Sent")
        sale = models.Sale.objects.first()
        sale.reminders_sent = 2
        sale.save()
        original_total = sale.total

        call_command(self.cron_name)

        # Validate sale info
        sale = models.Sale.objects.first()
        self.assertEqual(sale.reminders_sent, 3)

        # Get checkout link from email
        email_content = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(email_content, "html.parser")
        cta_link = soup.select_one(self.selectors["email_cta"])["href"]

        # Replace host wiuth test host in cta link
        cta_link = cta_link.replace(settings.HOST, self.live_server_url)

        # Open checkout link in selenium
        self.driver.get(cta_link)
        sleep(3)

        # Validate amount
        amount = self.driver.find_element(
            By.CSS_SELECTOR, self.selectors["checkout_amount"]
        ).text.replace("$", "")
        sale = models.Sale.objects.all()[0]
        self.assertEqual(float(amount), sale.total)
        self.assertEqual(float(amount), original_total * 0.85)

    @override_settings(PAYMENT_PROVIDER="stripe")
    def test_remainder_checkout_amount_discount_stripe(self):
        """Send discount on 3rd remainder"""

        # Update css selectors
        self.selectors["checkout_amount"] = 'img[alt="US"] + span.CurrencyAmount'

        # Create sale in "Reminder Sent" status
        models.Sale.objects.all().delete()
        self.__create_sale__("Reminder Sent")
        sale = models.Sale.objects.first()
        sale.reminders_sent = 2
        sale.save()
        original_total = sale.total

        call_command(self.cron_name)

        # Validate sale info
        sale = models.Sale.objects.first()
        self.assertEqual(sale.reminders_sent, 3)

        # Get checkout link from email
        email_content = mail.outbox[0].alternatives[0][0]
        soup = BeautifulSoup(email_content, "html.parser")
        cta_link = soup.select_one(self.selectors["email_cta"])["href"]

        # Replace host wiuth test host in cta link
        cta_link = cta_link.replace(settings.HOST, self.live_server_url)

        # Open checkout link in selenium
        self.driver.get(cta_link)
        sleep(3)

        # Validate amount
        amount = self.driver.find_element(
            By.CSS_SELECTOR, self.selectors["checkout_amount"]
        ).text.replace("$", "")
        sale = models.Sale.objects.all()[0]
        self.assertEqual(float(amount), sale.total)
        self.assertEqual(float(amount), original_total * 0.85)
