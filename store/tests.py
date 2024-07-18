from django.test import TestCase
from store import models
from django.utils import timezone


class FutureStockTestCase(TestCase):
    
    def setUp(self):
        """ Create initial data """
        self.today = timezone.now()
        self.tomorrow = self.today + timezone.timedelta(days=1)
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.tomorrow,
            added=False,
            amount=100,
        )
        self.endpoint = "/api/store/next-future-stock/"
    
    def test_get_next_future_stock(self):
        """ Test get next future stock """
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(
            json_data["next_future_stock"],
            self.tomorrow.strftime('%Y-%m-%d %H:%M:%S')
        )

    def test_get_next_future_stock_with_added(self):
        """ Test when future stock is already added and
        no more future stock to add """
        
        self.future_stock.added = True
        self.future_stock.save()
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(
            json_data["next_future_stock"],
            self.today.strftime('%Y-%m-%d %H:%M:%S')
        )