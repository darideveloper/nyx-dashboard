import re
import json
import base64

from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from store import models


def get_next_future_stock(request, email=""):
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
        
    already_subscribed = False
    user = models.User.objects.filter(email=email)
    if user:
        user = user[0]
        already_subscribed = models.FutureStockSubscription.objects.filter(
            user=user,
            future_stock=future_stock,
            active=True
        ).exists()
            
    return JsonResponse({
        'next_future_stock': next_future_stock_seconds,
        'already_subscribed': already_subscribed,
    })

    
@method_decorator(csrf_exempt, name='dispatch')
class FutureStockSubscription(View):
    
    def post(self, request):
        """ Subscribe to future stock """
        
        # Get json data
        json_data = json.loads(request.body)
        subscription_email = json_data.get('email')
        subscription_type = json_data.get('type')
        
        # Validate susbcription type
        if subscription_type not in ["add", "remove"]:
            return JsonResponse({
                'message': 'Invalid subscription type'
            }, status=400)
        
        # Get or create auth user
        users = models.User.objects.filter(email=subscription_email)
        if users:
            user = users[0]
        else:
            user = models.User.objects.create(
                email=subscription_email,
                username=subscription_email
            )
            
        # Get and validate future stock
        future_stock = models.FutureStock.objects.filter(
            added=False
        )
        if not future_stock:
            return JsonResponse({
                'message': 'Future stock not found'
            }, status=404)
        future_stock = future_stock[0]
        
        # Validate if user is already subscribed
        current_subscription = models.FutureStockSubscription.objects.filter(
            user=user,
            future_stock=future_stock
        )
        
        # Save subscription
        if subscription_type == "add":
            
            # reactivating subscription
            if current_subscription:
                current_subscription[0].active = True
                current_subscription[0].save()
            else:
                
                # Save subscription
                models.FutureStockSubscription.objects.create(
                    user=user,
                    future_stock=future_stock
                )
            return JsonResponse({
                'message': 'Subscribed to future stock'
            })
        else:
            # Deactivate subscription
            subscription = models.FutureStockSubscription.objects.filter(
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
                'message': 'Unsubscribed from future stock'
            })


@method_decorator(csrf_exempt, name='dispatch')
class Sale(View):
    
    def post(self, request):
        """ Sale sale from landing """
        
        # Get json data
        json_data = json.loads(request.body)
        
        # get image file in base64 and save
        logo_base64 = json_data.get('logo')
        if logo_base64:
        
            # Validate logo format
            match = re.match(r'data:image/(png|svg\+xml);base64,(.*)', logo_base64)
            if not match:
                return JsonResponse({
                    'message': 'Invalid logo format'
                }, status=400)

            # Get logo parts
            logo_file_type = match.group(1)
            logo_base64_string = match.group(2)
            if logo_file_type == "svg+xml":
                logo_file_type = "svg"
            logo_data = base64.b64decode(logo_base64_string)
            
            file_name = f'logo.{logo_file_type}'
            
            with open(file_name, 'wb') as f:
                f.write(logo_data)
        
        return JsonResponse({
            'message': 'Logo saved'
        })
            