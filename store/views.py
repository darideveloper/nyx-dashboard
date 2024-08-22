import re
import json
import base64

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect

from store import models
from utils.stripe import get_stripe_link


class NextFutureStock(View):
    
    def get(self, request, email=""):
        """ Return next future stock datetime
        
        Args:
            request (HttpRequest): Django request object
            email (str): User email to check if already subscribed
        """

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
        
        # Validate required fields
        required_fields = [
            "email", "set", "colors_num", "logo", "included_extras",
            "promo", "full_name", "country", "state", "city",
            "postal_code", "street_address", "phone"
        ]
        for field in required_fields:
            if field not in json_data:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Missing field: {field}',
                    'data': {}
                }, status=400)

        # Get info
        email = json_data['email']
        set = json_data['set']
        colors_num = json_data['colors_num']
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
        
        # Generate colors instances
        colors = {
            "color_set": json_data['set_color'],
            "logo_color_1": json_data['logo_color_1'],
            "logo_color_2": json_data['logo_color_2'],
            "logo_color_3": json_data['logo_color_3'],
        }
        colors_instances = {}
        for color_key, color_name in colors.items():
            color_obj, _ = models.Color.objects.get_or_create(name=color_name)
            colors_instances[color_key] = color_obj
        
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
        
        promo_type = promo['discount']['type']
        promo_value = promo['discount']['value']
        promo_type_obj, _ = models.PromoCodeType.objects.get_or_create(
            name=promo_type
        )
        
        promo_obj, _ = models.PromoCode.objects.get_or_create(
            code=promo['code'],
            discount=promo_value,
            type=promo_type_obj,
        )
        
        # Calculate total
        total = 0
        total += set_obj.price
        total += colors_num_obj.price
        for addon in addons_objs:
            total += addon.price
        total -= promo_obj.discount
        total = round(total, 2)
        
        # Get status
        status, _ = models.SaleStatus.objects.get_or_create(value="Pending")
        
        # Save sale
        sale = models.Sale.objects.create(
            user=user,
            set=set_obj,
            colors_num=colors_num_obj,
            color_set=colors_instances['color_set'],
            promo_code=promo_obj,
            full_name=full_name,
            country=country,
            state=state,
            city=city,
            postal_code=postal_code,
            street_address=street_address,
            phone=phone,
            total=total,
            status=status,
        )
        
        # Add extra colors
        if colors_num['num'] >= 2:
            sale.logo_color_1 = colors_instances['logo_color_1']
        if colors_num['num'] >= 3:
            sale.logo_color_2 = colors_instances['logo_color_2']
        if colors_num['num'] == 4:
            sale.logo_color_3 = colors_instances['logo_color_3']
        sale.save()
        
        # Set addons
        sale.addons.set(addons_objs)

        # get image file in base64 and save
        if logo_base64:

            # Validate logo format
            match = re.match(
                r'data:image/(png|svg\+xml);base64,(.*)', logo_base64)
            if not match:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid logo format',
                    'data': {}
                }, status=400)

            # Get logo parts
            logo_file_type = match.group(1)
            logo_base64_string = match.group(2)
            if logo_file_type == "svg+xml":
                logo_file_type = "svg"
            logo_data = base64.b64decode(logo_base64_string)
            
            # Create a file name
            file_name = f'sale_{sale.id}_logo.{logo_file_type}'

            # Save the logo file
            sale.logo.save(file_name, ContentFile(logo_data))
            
        # Ggenerate strip link
        product_name = f"Tracker {set_obj.name} {colors_num_obj.num} colors"
        description = ""
        description += f"Set: {set_obj.name} | "
        description += f"Colors: {colors_num_obj.num} | "
        description += f"Client Email: {email} | "
        description += f"Client Full Name: {full_name} | "
        
        # Validate stok
        current_stock = models.StoreStatus.objects.filter(
            key='current_stock'
        ).first()
        current_stock_value = int(current_stock.value) if current_stock else 0
        if current_stock_value <= 0:
            return JsonResponse({
                "status": "error",
                "message": "No stock available",
                "data": {}
            }, status=400)
        
        stripe_link = get_stripe_link(
            product_name,
            total,
            description,
            email,
            sale.id
        )
        
        return JsonResponse({
            "status": "success",
            "message": "Sale saved",
            "data": {
                "stripe_link": stripe_link,
            },
        })
        

class CurrentStock(View):
    
    def get(self, request):
        """ Get current stock """
        
        current_stock = models.StoreStatus.objects.get(key='current_stock')
        current_stock_int = int(current_stock.value)
        
        return JsonResponse({
            "status": "success",
            "message": "Current stock",
            "data": {
                "current_stock": current_stock_int
            }
        })


class SaleDone(View):
    
    def get(self, request, sale_id: str):
        """ Update sale status and redirect to landing
        
        Args:
            request (HttpRequest): Django request object
            sale_id (str): sale id from url
        """
        
        landing_done_page = settings.LANDING_HOST
        
        # Get sale
        sale = models.Sale.objects.filter(id=sale_id).first()
        if not sale:
            landing_done_page += f"?sale-id={sale_id}&sale-status=error"
            return redirect(landing_done_page)
        
        # Update status
        status, _ = models.SaleStatus.objects.get_or_create(value="Paid")
        sale.status = status
        sale.save()
        
        # Update stock
        current_stock, _ = models.StoreStatus.objects.get_or_create(key='current_stock')
        current_stock_int = int(current_stock.value)
        current_stock.value = str(current_stock_int - 1)
        current_stock.save()
        
        # TODO: Confirmation email afrter payment
        
        landing_done_page += f"?sale-id={sale_id}&sale-status=success"
        return redirect(landing_done_page)