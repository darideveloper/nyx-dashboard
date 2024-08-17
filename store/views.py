import re
import json
import base64

from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

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

        sample_data = {
            "email": "darideveloper@gmail.com",
            "set": {
                "name": "basic",
                "points": 5,
                "price": 275,
                "recommended": False,
                "logos": 5
            },
            "colors_num": {
                "num": 4,
                "price": 20,
                "details": "4 Colors (Trackers and 3 logo colors) +20USD"
            },
            "set_color": "blue",
            "logo_color_1": "white",
            "logo_color_2": "grey",
            "logo_color_3": "green",
            "logo": "",
            "included_extras": [
                [
                    {
                        "name": "Wifi 2.4ghz USB Dongle",
                        "price": 14,
                        "exclude_sets": []
                    },
                    {
                        "name": "Straps",
                        "price": 25,
                        "exclude_sets": []
                    }
                ]
            ],
            "promo": {
                "code": "DARI",
                "discount": 10
            },
            "full_name": "dari",
            "country": "dev",
            "state": "street",
            "city": "ags",
            "postal_code": "20010",
            "street_address": "street 1",
            "phone": "12323123"
        }

        # Get json data
        json_data = json.loads(request.body)

        # Get info
        email = json_data['email']
        set = json_data['set']
        colors_num = json_data['colors_num']
        color_set = json_data['set_color']
        logo_color_1 = json_data['logo_color_1']
        logo_color_2 = json_data['logo_color_2']
        logo_color_3 = json_data['logo_color_3']
        logo_base64 = json_data['logo']
        addons = json_data['included_extras']
        promo = json_data['promo']
        full_name = json_data['full_name']
        country = json_data['country']
        state = json_data['state']
        city = json_data['city']
        postal_code = json_data['postal_code']
        street_address = json_data['street_address']
        phone = json_data['phone']
        
        # Get user or create a new one
        user, created = User.objects.get_or_create(email=email)
        if created:
            # Save email as username
            user.username = email
            user.save()
            
            # TODO: send invitation email
        
        # Save aditional models
        set_obj, _ = models.Set.objects.get_or_create(
            name=set['name'],
            points=set['points'],
            price=set['price'],
            recommended=set['recommended'],
            logos=set['logos']
        )
        
        colors_num_obj, _ = models.ColorsNum.objects.get_or_create(
            num=colors_num['num'],
            price=colors_num['price'],
            details=colors_num['details']
        )
        
        addons_objs = []
        for addon in addons:
            addon_obj, _ = models.Addon.objects.get_or_create(
                name=addon['name'],
                price=addon['price']
            )
            addons_objs.append(addon_obj)
            
        promo_obj, _ = models.PromoCodes.objects.get_or_create(
            code=promo['code'],
            discount=promo['discount']
        )
        
        # Calculate total
        total = 0
        total += set_obj.price
        total += colors_num_obj.price
        for addon in addons_objs:
            total += addon.price
        # TODO: calculate discount
        # total -= promo_obj.discount
        total = round(total, 2)
        
        # Save sale
        models.Sale.objects.create(
            user=user,
            set=set_obj,
            colors_num=colors_num_obj,
            color_set=color_set,
            logo_color_1=logo_color_1,
            logo_color_2=logo_color_2,
            logo_color_3=logo_color_3,
            addons=addons_objs,
            promo_code=promo_obj,
            full_name=full_name,
            country=country,
            state=state,
            city=city,
            postal_code=postal_code,
            street_address=street_address,
            phone=phone,
            total=total
        )

        # # get image file in base64 and save
        # if logo_base64:

        #     # Validate logo format
        #     match = re.match(
        #         r'data:image/(png|svg\+xml);base64,(.*)', logo_base64)
        #     if not match:
        #         return JsonResponse({
        #             'message': 'Invalid logo format'
        #         }, status=400)

        #     # Get logo parts
        #     logo_file_type = match.group(1)
        #     logo_base64_string = match.group(2)
        #     if logo_file_type == "svg+xml":
        #         logo_file_type = "svg"
        #     logo_data = base64.b64decode(logo_base64_string)

        #     file_name = f'logo.{logo_file_type}'

        #     with open(file_name, 'wb') as f:
        #         f.write(logo_data)

        return JsonResponse({
            "status": "success",
            "message": "Sale saved",
            "data": {}
        })
