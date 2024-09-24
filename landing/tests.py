import os

from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from landing import models
from utils.media import get_media_url


class LandingViewsTest(TestCase):
    
    def setUp(self):
        """ Create data for testing """
        
        # Paths
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        media_path = os.path.join(project_path, 'media')
        media_test_path = os.path.join(media_path, 'test')

        # Create category
        self.category = models.Category.objects.create(
            name='test_category'
        )

        # Create texts
        self.texts = []
        for text_index in range(1, 3):
            text = models.Text.objects.create(
                key=f'test_key_{text_index}',
                value=f'test_value_{text_index}',
                link='http://test.com',
                category=self.category
            )
            self.texts.append(text)

        # Create images
        self.images = []
        for image_index in range(1, 3):
            image = models.Image.objects.create(
                key=f'test_key_{image_index}',
                category=self.category,
                link='http://test.com'
            )
            image_path = os.path.join(media_test_path, f'test_image_{image_index}.jpg')
            image_file = SimpleUploadedFile(
                name=f'test_image_{image_index}.jpg',
                content=open(image_path, 'rb').read(),
                content_type='image/jpeg'
            )
            image.image = image_file
            image.save()
            self.images.append(image)
            
        # Create videos
        self.videos = []
        for video_index in range(1, 3):
            video = models.Video.objects.create(
                key=f'test_key_{video_index}',
                category=self.category
            )
            video_path = os.path.join(media_test_path, f'test_video_{video_index}.mp4')
            video_file = SimpleUploadedFile(
                name=f'test_video_{video_index}.mp4',
                content=open(video_path, 'rb').read(),
                content_type='video/mp4'
            )
            video.video = video_file
            video.save()
            self.videos.append(video)

        self.api_base = "/api/landing"

    def test_get_texts(self):
        """ Get data from text api, and validate json response """

        # Request api and validate response
        response = self.client.get(f"{self.api_base}/texts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Validate json content
        json_data_response = response.json()["texts"]
        json_data_expected = []
        for text in self.texts:
            json_data_expected.append({
                'key': text.key,
                'value': text.value,
                'link': text.link,
                'category': self.category.name
            })
        
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
        json_data_expected = []
        for image in self.images:
            json_data_expected.append({
                'key': image.key,
                'image': get_media_url(image.image.url),
                'category': self.category.name,
                'link': image.link
            })
        
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
        json_data_expected = []
        for video in self.videos:
            json_data_expected.append({
                'key': video.key,
                'video': get_media_url(video.video.url),
                'category': self.category.name
            })
        
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
        json_data_expected = {}
        
        expected_texts = []
        for text in self.texts:
            expected_texts.append({
                'key': text.key,
                'value': text.value,
                'link': text.link,
                'category': self.category.name
            })
        
        expected_images = []
        for image in self.images:
            expected_images.append({
                'key': image.key,
                'image': get_media_url(image.image.url),
                'category': self.category.name,
                'link': image.link
            })
            
        expected_videos = []
        for video in self.videos:
            expected_videos.append({
                'key': video.key,
                'video': get_media_url(video.video.url),
                'category': self.category.name
            })
            
        json_data_expected["texts"] = expected_texts
        json_data_expected["images"] = expected_images
        json_data_expected["videos"] = expected_videos
        
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