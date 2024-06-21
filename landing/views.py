from django.shortcuts import redirect
from django.http import JsonResponse
from landing import models


def home(request):
    """ Redirect to admin """
    return redirect('/admin/')


def TextApi(request):
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