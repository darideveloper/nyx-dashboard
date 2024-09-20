import json

from django.http import JsonResponse
from django.shortcuts import redirect

from landing import models
from utils.media import get_media_url


def home(request):
    """ Redirect to admin """
    return redirect('/admin/')


def get_texts(request):
    """ Return all texts as json """
    
    texts = models.Text.objects.all()
    texts_data = list(map(lambda text: {
        'key': text.key,
        'value': text.value,
        'link': text.link,
        'category': text.category.name
    }, texts))
    
    return JsonResponse({
        "texts": texts_data
    })
    
    
def get_images(request):
    """ Return all images as json """
    
    images = models.Image.objects.all()
    images_data = list(map(lambda image: {
        'key': image.key,
        'image': get_media_url(image.image),
        'category': image.category.name,
        'link': image.link,
    }, images))
    
    return JsonResponse({
        "images": images_data
    })
    

def get_videos(request):
    """ Return all videos as json """
    
    videos = models.Video.objects.all()
    videos_data = list(map(lambda video: {
        'key': video.key,
        'video': get_media_url(video.video),
        'category': video.category.name
    }, videos))
    
    return JsonResponse({
        "videos": videos_data
    })
    
    
def get_batch(requests):
    """ return data from all models """
    
    texts = get_texts(requests).content
    images = get_images(requests).content
    videos = get_videos(requests).content
    
    texts_json = json.loads(texts)["texts"]
    images_json = json.loads(images)["images"]
    videos_json = json.loads(videos)["videos"]
    
    return JsonResponse({
        "texts": texts_json,
        "images": images_json,
        "videos": videos_json
    })