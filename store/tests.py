from django.test import TestCase
from store import models
from django.utils import timezone


class FutureStockTestCase(TestCase):
    
    def setUp(self):
        """ Create initial data """
        self.today = timezone.now()
        self.future_stock = models.FutureStock.objects.create(
            datetime=self.today + timezone.timedelta(
                days=3, hours=2, minutes=30, seconds=15
            ),
            added=False,
            amount=100,
        )
        self.endpoint = "/api/store/next-future-stock/"
    
    def test_get_next_future_stock(self):
        """ Test get next future stock """
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["days"], 3)
        self.assertEqual(json_data["hours"], 2)
        self.assertEqual(json_data["minutes"], 30)
        self.assertTrue(json_data["seconds"] <= 15)
        
    def test_get_next_future_stock_with_added(self):
        """ Test when future stock is already added and
        no more future stock to add """
        
        self.future_stock.added = True
        self.future_stock.save()
        
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
        })