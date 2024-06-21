from django.test import TestCase
from landing import models


class LandingViewsTestCase(TestCase):
    
    def setUp(self):
        pass
    
    def test_home(self):
        """ Load home page, and validate redirect to admin """
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        
    def test_text_api(self):
        """ Get data from text api, and validate json response """
        
        # Add text to table
        text_1 = models.Text.objects.create(
            key='test_key_1',
            value='test_value_1',
            link='http://test.com'
        )
        
        text_2 = models.Text.objects.create(
            key='test_key_2',
            value='test_value_2',
            link=''
        )
        
        # Request api and validate response
        response = self.client.get('/api/texts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        json_data_expected = [
            {
                'key': text_1.key,
                'value': text_1.value,
                'link': text_1.link
            },
            {
                'key': text_2.key,
                'value': text_2.value,
                'link': text_2.link
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)
        
    def test_text_api_no_data(self):
        """ Get data from text api, without text, and
        validate json response (json empty list) """
        
        # Request api and validate response
        response = self.client.get('/api/texts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        self.assertEqual(json_data_response, [])