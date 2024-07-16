from django.core.management import call_command
from django.test import TestCase
from store import models
from django.utils import timezone


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
        
        self.cron_name = "future_stock_update_status"

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
