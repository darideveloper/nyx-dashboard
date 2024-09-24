import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from store import models


class FutureStockUpdateTest(TestCase):
    def setUp(self):
        # Create initial status
        self.current_stock = models.StoreStatus.objects.create(
            key='current_stock',
            value='0'
        )
        
        # Create future stocks
        self.future_stock = models.FutureStock.objects.create(
            amount=5,
            datetime=timezone.now() - timezone.timedelta(days=1),
            added=False
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
            future_stock=self.future_stock,
            user=self.user
        )
            
        self.cron_name = "future_stock_update"

    def test_datetime_reached(self):
        """ Test add stock when future stock datetime is reached """
        
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
        """ Test add stock when future stock datetime is reached
        but subscription is inactive """
        
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
        """ Test add stock when future stock datetime is reached
        but the user its new (from landing) """
        
        # Delete original user
        self.user.delete()

        user_email = "new@test.com"
        res = self.client.post(
            "/api/store/future-stock-subscription/",
            data=json.dumps({
                "email": user_email,
                "type": "add",
            }),
            content_type="application/json"
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
        """ Test add stock when future stock datetime is not reached """
        
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


class PaymentReminderTest(TestCase):
    def setUp(self):
        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com"
        )
        
        self.__create_sale__("Pending")
        
        self.cron_name = "payment_reminder"
        
        # Create data with command
        call_command("apps_loaddata")
        
    def __create_sale__(self, status_str: str):
        """ Create new sale with spaecified status
        
        Args:
            status_str (str): Sale status value
        """
        
        # Create sale
        set, _ = models.Set.objects.get_or_create(
            name="set name",
            points=5,
            price=275,
            recommended=False,
            logos=5
        )
        
        colors_num, _ = models.ColorsNum.objects.get_or_create(
            num=4,
            price=20,
            details="4 Colors (Trackers and 3 logo colors) +20USD"
        )
        
        color, _ = models.Color.objects.get_or_create(name="blue")
        status, _ = models.SaleStatus.objects.get_or_create(value=status_str)
         
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
    
    def test_send_remainder(self):
        """ Send remainder email and validate content """
        
        call_command(self.cron_name)
        
        # Validte single email sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email main data
        sent_email = mail.outbox[0]
        subject = "Don't forget to pay for your order!"
        cta_text = "Pay now"
        self.assertEqual(sent_email.subject, subject)
        self.assertIn(cta_text, sent_email.body)
        
        # Vdalite email html
        cta_link = "checkout.stripe.com"
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link, email_html)
        
        # Validate sale info
        sale = models.Sale.objects.first()
        self.assertEqual(sale.status.value, "Reminder Sent")
        self.assertEqual(sale.reminders_sent, 1)
    
    def test_send_multiple_remainders(self):
        """ Send 2 remainder emails """
        
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
        """ No send remainder where there are no sales pending """
        
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
        """ No send remainder when 3 reminders have been sent """
        
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
        
    