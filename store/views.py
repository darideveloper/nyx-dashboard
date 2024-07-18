from django.http import JsonResponse
from store import models
from django.utils import timezone


def get_next_future_stock(request):
    """ Return next future stock datetime """
    
    future_stock = models.FutureStock.objects.filter(
        added=False
    ).order_by('datetime').first()
    now = timezone.now()
    next_future_stock = future_stock.datetime if future_stock else now
    next_future_stock_seconds = int((next_future_stock - now).total_seconds())
            
    return JsonResponse({
        'next_future_stock': next_future_stock_seconds
    })
    
    