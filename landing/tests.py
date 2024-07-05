from django.test import TestCase
from landing import models


class LandingViewsTestCase(TestCase):
    
    def setUp(self):
        pass
    
    def test_home(self):
        """ Load home page, and validate redirect to admin """
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        
    def test_get_texts(self):
        """ Get data from text api, and validate json response """
        
        category = models.category.objects.create(
            name='test_category'
        )
        
        # Add text to table
        text_1 = models.Text.objects.create(
            key='test_key_1',
            value='test_value_1',
            link='http://test.com',
            category=category
        )
        
        text_2 = models.Text.objects.create(
            key='test_key_2',
            value='test_value_2',
            link='',
            category=category
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
                'link': text_1.link,
                'category': category.name
            },
            {
                'key': text_2.key,
                'value': text_2.value,
                'link': text_2.link,
                'category': category.name
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)
        
    def test_get_texts_no_data(self):
        """ Get data from text api, without text, and
        validate json response (json empty list) """
        
        # Request api and validate response
        response = self.client.get('/api/texts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        self.assertEqual(json_data_response, [])
        
    def test_get_images(self):
        """ Get data from image api, and validate json response """
        
        category = models.category.objects.create(
            name='test_category'
        )
        
        # Add text to table
        image_1 = models.Image.objects.create(
            key='test_key_1',
            image='images/test_image_1.jpg',
            category=category,
            link='http://test.com'
        )
        
        image_2 = models.Image.objects.create(
            key='test_key_2',
            image='images/test_image_2.jpg',
            category=category
        )
        
        # Request api and validate response
        response = self.client.get('/api/images/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        json_data_expected = [
            {
                'key': image_1.key,
                'image': image_1.image.url,
                'category': category.name,
                'link': image_1.link
            },
            {
                'key': image_2.key,
                'image': image_2.image.url,
                'category': category.name,
                'link': None
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)
        
    def test_get_images_no_data(self):
        """ Get data from text api, without images, and
        validate json response (json empty list) """
        
        # Request api and validate response
        response = self.client.get('/api/images/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        self.assertEqual(json_data_response, [])
        
    def test_get_videos(self):
        """ Get data from image api, and validate json response """
        
        category = models.category.objects.create(
            name='test_category'
        )
        
        # Add text to table
        video_1 = models.Video.objects.create(
            key='test_key_1',
            video='videos/test_video_1.mp4',
            category=category
        )
        
        video_2 = models.Video.objects.create(
            key='test_key_2',
            video='videos/test_video_2.mp4',
            category=category
        )
        
        # Request api and validate response
        response = self.client.get('/api/videos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        json_data_expected = [
            {
                'key': video_1.key,
                'video': video_1.video.url,
                'category': category.name
            },
            {
                'key': video_2.key,
                'video': video_2.video.url,
                'category': category.name
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)
        
    def test_get_videos_no_data(self):
        """ Get data from text api, without videos, and
        validate json response (json empty list) """
        
        # Request api and validate response
        response = self.client.get('/api/videos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Validate json content
        json_data_response = response.json()["data"]
        self.assertEqual(json_data_response, [])