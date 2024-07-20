import json
from store import models
from django.utils import timezone
from django.http import JsonResponse
from django.views import View


def get_next_future_stock(request):
    """ Return next future stock datetime """
    
    future_stock = models.FutureStock.objects.filter(
        added=False
    ).order_by('datetime').first()
    now = timezone.now()
    extra_minutes = 10
    next_future_stock = future_stock.datetime if future_stock else now
    next_future_stock_seconds = int((next_future_stock - now).total_seconds())
    if next_future_stock_seconds:
        next_future_stock_seconds += extra_minutes * 60
            
    return JsonResponse({
        'next_future_stock': next_future_stock_seconds
    })
    
    
class FutureStockSubscription(View):
    
    def post(self, request):
        """ Subscribe to future stock """
        
        # Get json data
        print("request.body", request.body)
        json_data = json.loads(request.body)
        subscription_email = json_data.get('email')
        subscription_type = json_data.get('type')
        subscription_stock_id = json_data.get('stock_id')
        
        # Validate susbcription type
        if subscription_type not in ["add", "remove"]:
            return JsonResponse({
                'message': 'Invalid subscription type'
            }, status=400)
        
        # Get or create auth user
        user, _ = models.User.objects.get_or_create(
            email=subscription_email,
            username=subscription_email
        )

        # Get and validate future stock
        future_stock = models.FutureStock.objects.filter(
            id=subscription_stock_id
        )
        if not future_stock:
            return JsonResponse({
                'message': 'Future stock not found'
            }, status=404)
        future_stock = future_stock[0]
        
        # Save subscription
        if subscription_type == "add":
            models.FutureStockSubcription.objects.create(
                user=user,
                future_stock=future_stock
            )
        else:
            subscription = models.FutureStockSubcription.objects.filter(
                user=user,
                future_stock=future_stock
            )
            if not subscription:
                return JsonResponse({
                    'message': 'Subscription not found'
                }, status=404)
            subscription = subscription[0]
            subscription.active = False
            subscription.save()
        
        return JsonResponse({
            'message': 'Subscribed to future stock'
        })