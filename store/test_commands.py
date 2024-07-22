import os

from dotenv import load_dotenv
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.core import mail

from store import models

# Env variables
load_dotenv()
LANDING_HOST = os.getenv("LANDING_HOST")


class UpdateStockCommandTestCase(TestCase):
    def setUp(self):
        # Create initial status
        self.current_stock = models.Status.objects.create(
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
        self.subscription = models.FutureStockSubcription.objects.create(
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
        cta_link_base = f"{LANDING_HOST}#buy-form"
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
