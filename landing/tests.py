from django.test import TestCase
from landing import models
from utils.media import get_media_url


class LandingViewsTestCase(TestCase):
    
    def setUp(self):
        """ Create data for testing """

        # Create category
        self.category = models.Category.objects.create(
            name='test_category'
        )

        # Create texts
        self.text_1 = models.Text.objects.create(
            key='test_key_1',
            value='test_value_1',
            link='http://test.com',
            category=self.category
        )

        self.text_2 = models.Text.objects.create(
            key='test_key_2',
            value='test_value_2',
            link='',
            category=self.category
        )

        # Create images
        self.image_1 = models.Image.objects.create(
            key='test_key_1',
            image='/media/images/test_image_1.jpg',
            category=self.category,
            link='http://test.com'
        )

        self.image_2 = models.Image.objects.create(
            key='test_key_2',
            image='/media/images/test_image_2.jpg',
            category=self.category
        )

        # Create videos
        self.video_1 = models.Video.objects.create(
            key='test_key_1',
            video='/media/videos/test_video_1.mp4',
            category=self.category
        )

        self.video_2 = models.Video.objects.create(
            key='test_key_2',
            video='/media/videos/test_video_2.mp4',
            category=self.category
        )
        
        self.api_base = "/api/landing"

    def test_get_texts(self):
        """ Get data from text api, and validate json response """

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/texts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["texts"]
        json_data_expected = [
            {
                'key': self.text_1.key,
                'value': self.text_1.value,
                'link': self.text_1.link,
                'category': self.category.name
            },
            {
                'key': self.text_2.key,
                'value': self.text_2.value,
                'link': self.text_2.link,
                'category': self.category.name
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)

    def test_get_texts_no_data(self):
        """ Get data from text api, without text, and
        validate json response (json empty list) """

        # Delete texts
        models.Text.objects.all().delete()

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/texts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["texts"]
        self.assertEqual(json_data_response, [])

    def test_get_images(self):
        """ Get data from image api, and validate json response """

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/images/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["images"]
        json_data_expected = [
            {
                'key': self.image_1.key,
                'image': get_media_url(self.image_1.image.url),
                'category': self.category.name,
                'link': self.image_1.link
            },
            {
                'key': self.image_2.key,
                'image': get_media_url(self.image_2.image.url),
                'category': self.category.name,
                'link': None
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)

    def test_get_images_no_data(self):
        """ Get data from text api, without images, and
        validate json response (json empty list) """

        # Delete images
        models.Image.objects.all().delete()

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/images/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["images"]
        self.assertEqual(json_data_response, [])

    def test_get_videos(self):
        """ Get data from image api, and validate json response """

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/videos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["videos"]
        json_data_expected = [
            {
                'key': self.video_1.key,
                'video': get_media_url(self.video_1.video.url),
                'category': self.category.name
            },
            {
                'key': self.video_2.key,
                'video': get_media_url(self.video_2.video.url),
                'category': self.category.name
            }
        ]
        self.assertEqual(json_data_response, json_data_expected)

    def test_get_videos_no_data(self):
        """ Get data from text api, without videos, and
        validate json response (json empty list) """

        # Delete videos
        models.Video.objects.all().delete()

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/videos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["videos"]
        self.assertEqual(json_data_response, [])

    def test_get_batch(self):
        """ get data from all models, and validate json response """

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/batch/")
                
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()
        json_data_expected = {
            "texts": [
                {
                    'key': self.text_1.key,
                    'value': self.text_1.value,
                    'link': self.text_1.link,
                    'category': self.category.name
                },
                {
                    'key': self.text_2.key,
                    'value': self.text_2.value,
                    'link': self.text_2.link,
                    'category': self.category.name
                }
            ],
            "images": [
                {
                    'key': self.image_1.key,
                    'image': get_media_url(self.image_1.image.url),
                    'category': self.category.name,
                    'link': self.image_1.link
                },
                {
                    'key': self.image_2.key,
                    'image': get_media_url(self.image_2.image.url),
                    'category': self.category.name,
                    'link': None
                }
            ],
            "videos": [
                {
                    'key': self.video_1.key,
                    'video': get_media_url(self.video_1.video.url),
                    'category': self.category.name
                },
                {
                    'key': self.video_2.key,
                    'video': get_media_url(self.video_2.video.url),
                    'category': self.category.name
                }
            ]
        }
        self.assertEqual(json_data_response["texts"], json_data_expected["texts"])
        self.assertEqual(json_data_response["images"], json_data_expected["images"])
        self.assertEqual(json_data_response["videos"], json_data_expected["videos"])

    def test_get_batch_no_data(self):
        
        # Delete all data
        models.Text.objects.all().delete()
        models.Image.objects.all().delete()
        models.Video.objects.all().delete()

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/batch/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()
        json_data_expected = {
            "texts": [],
            "images": [],
            "videos": []
        }
        self.assertEqual(json_data_response, json_data_expected)