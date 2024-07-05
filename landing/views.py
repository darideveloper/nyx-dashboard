from django.shortcuts import redirect
from django.http import JsonResponse
from landing import models


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
        "data": texts_data
    })
    
    
def get_images(request):
    """ Return all images as json """
    
    images = models.Image.objects.all()
    images_data = list(map(lambda image: {
        'key': image.key,
        'image': image.image.url,
        'category': image.category.name,
        'link': image.link
    }, images))
    
    return JsonResponse({
        "data": images_data
    })
    

def get_videos(request):
    """ Return all videos as json """
    
    videos = models.Video.objects.all()
    videos_data = list(map(lambda video: {
        'key': video.key,
        'video': video.video.url,
        'category': video.category.name
    }, videos))
    
    return JsonResponse({
        "data": videos_data
    })