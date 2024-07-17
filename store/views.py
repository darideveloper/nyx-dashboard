from django.http import JsonResponse
from store import models
from django.utils import timezone


def get_next_future_stock(request):
    """ Return next future stock datetime """
    
    future_stock = models.FutureStock.objects.filter(
        added=False
    ).order_by('datetime').first()
    today = timezone.now()
    countdown = {
        "days": 0,
        "hours": 0,
        "minutes": 0,
        "seconds": 0,
    }
    if future_stock:
        countdown_delta = future_stock.datetime - today
        countdown["days"] = countdown_delta.days
        countdown["hours"] = countdown_delta.seconds // 3600
        countdown["minutes"] = countdown_delta.seconds // 60 % 60
        countdown["seconds"] = countdown_delta.seconds % 60
        
    return JsonResponse(countdown)
    
    