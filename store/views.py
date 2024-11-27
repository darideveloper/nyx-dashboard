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
from utils.emails import send_email
from utils.media import get_media_url
from utils.stripe import get_stripe_link_sale, get_stripe_transaction_link


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
        next_future_stock_seconds = int(
            (next_future_stock - now).total_seconds())
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
        comments = json_data.get('comments', "")

        # Generate colors instances
        colors = {
            "color_set": json_data['set_color'],
            "logo_color_1": json_data['logo_color_1'],
            "logo_color_2": json_data['logo_color_2'],
            "logo_color_3": json_data['logo_color_3'],
        }
        colors_instances = {}
        for color_key, color_name in colors.items():
            color_obj = models.Color.objects.get(name=color_name)
            colors_instances[color_key] = color_obj

        # Get user or create a new one
        user, created = User.objects.get_or_create(email=email)
        if created:
            # Save email as username
            user.username = email
            user.is_active = False
            user.is_staff = True
            self.password = User.objects.make_random_password()
            user.set_password(self.password)
            user.save()

            # Send invitation email
            email_texts = [
                "Welcome to Nyx Trackers!",
                "We are glad you are here.",
                "You sale has been saved.",
                "If you want to check your order status, you can do it in the dashboard."
                " Just complete your registration, and you will be able to see all your"
                " orders in one place and in real time."
            ]
            send_email(
                subject="Nyx Trackers Complete your registration",
                first_name=user.first_name,
                last_name=user.last_name,
                texts=email_texts,
                cta_link=f"{settings.HOST}/sign-up/",
                cta_text="Complete registration",
                to_email=user.email,
            )

        # Save aditional models
        set_obj = models.Set.objects.get(
            name=set,
        )

        colors_num_obj = models.ColorsNum.objects.get(
            num=colors_num,
        )

        addons_objs = []
        for addon in addons:
            addon_obj = models.Addon.objects.get(
                name=addon,
            )
            addons_objs.append(addon_obj)

        promo_type = promo['discount']['type']
        promo_value = promo['discount']['value']
        promo_type_obj = models.PromoCodeType.objects.get(
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
        status = models.SaleStatus.objects.get(value="Pending")

        # Validate if user has a pending order
        pending_sales = models.Sale.objects.filter(
            user=user,
            status__value="Pending"
        )

        # Create new sale
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
            comments=comments,
        )
        
        # Validate stock
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

        # Delete old pending sales
        if pending_sales:
            
            pending_sales.delete()

            # Submit email to user
            send_email(
                subject="Nyx Trackers Sale Updated",
                first_name=user.first_name,
                last_name=user.last_name,
                texts=[
                    "Your sale has been updated.",
                    "You will get an email confirmation after payment.",
                    "Sign up to check your order status in the dashboard.",
                ],
                cta_link=f"{settings.HOST}/sign-up",
                cta_text="Sign up",
                to_email=user.email,
            )

            # Submit email to admin
            send_email(
                subject="Nyx Trackers Sale Updated by User",
                first_name="Admin",
                last_name="",
                texts=[
                    f"The sale {sale.id} has been updated by the user {
                        user.email}.",
                    "Check the sale in the dashboard.",
                ],
                cta_link=f"{settings.HOST}/admin/store/sale/{sale.id}/change/",
                cta_text="View sale in dashboard",
                to_email=settings.ADMIN_EMAIL,
            )

        # Add extra colors
        if colors_num >= 2:
            sale.logo_color_1 = colors_instances['logo_color_1']
        if colors_num >= 3:
            sale.logo_color_2 = colors_instances['logo_color_2']
        if colors_num == 4:
            sale.logo_color_3 = colors_instances['logo_color_3']
        sale.save()

        # Set addons
        sale.addons.clear()
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

        stripe_link = get_stripe_link_sale(sale)

        return JsonResponse({
            "status": "success",
            "message": "Sale saved",
            "data": {
                "stripe_link": stripe_link,
            },
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

        # Get link from stripe
        stripe_link = get_stripe_transaction_link(sale.total)
        if not stripe_link:
            stripe_link = "Error getting stripe link"
        sale.stripe_link = stripe_link

        # Update status
        status = models.SaleStatus.objects.get(value="Paid")
        sale.status = status
        sale.save()

        # Update stock
        current_stock = models.StoreStatus.objects.get(key='current_stock')
        current_stock_int = int(current_stock.value)
        current_stock.value = str(current_stock_int - 1)
        current_stock.save()

        # Get sale data
        sale_data = sale.get_sale_data_dict()

        email_texts = [
            "Your payment has been confirmed!",
            "Your order is being processed.",
            "You will receive notifications about the status of your order.",
            "Here your order details:"
        ]

        logo_url = get_media_url(sale.logo.url) if sale.logo else ""

        # Confirmation email afrter payment
        send_email(
            subject="Nyx Trackers Payment Confirmation",
            first_name=sale.user.first_name,
            last_name=sale.user.last_name,
            texts=email_texts,
            cta_link=f"{settings.HOST}/admin/",
            cta_text="Go to dashboard",
            to_email=sale.user.email,
            key_items=sale_data,
            image_src=logo_url
        )

        # Send email to admin
        send_email(
            subject="Nyx Trackers New Sale",
            first_name="Admin",
            last_name="",
            texts=["A new sale has been made."],
            cta_link=f"{settings.HOST}/admin/store/sale/{sale_id}/change/",
            cta_text="View sale in dashboard",
            to_email=settings.ADMIN_EMAIL,
            key_items=sale_data,
            image_src=logo_url
        )

        landing_done_page += f"?sale-id={sale_id}&sale-status=success"
        return redirect(landing_done_page)


@method_decorator(csrf_exempt, name='dispatch')
class PromoCode(View):

    def post(self, request):
        """ Validate promo code """

        # Get promo code value form json data
        json_data = json.loads(request.body)
        promo_code = json_data.get('promo_code')

        # Check if promo code exists
        promo = models.PromoCode.objects.filter(code=promo_code)
        if not promo:
            return JsonResponse({
                "status": "error",
                "message": "Invalid promo code",
                "data": {}
            }, status=404)

        promo = promo[0]

        # Return promo count discount and type
        return JsonResponse({
            "status": "success",
            "message": "Valid promo code",
            "data": {
                "value": promo.discount,
                "type": promo.type.name,
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class PendingOder(View):

    def post(self, request):
        """ Check if user has pending orders """

        # Get user's email from json
        json_data = json.loads(request.body)
        email = json_data.get('email')

        # Get user
        user = models.User.objects.filter(email=email)

        # Validate user and Check if user has pending orders
        has_pending_order = None
        if user:
            user = user[0]
            has_pending_order = models.Sale.objects.filter(
                user=user,
                status__value="Pending"
            )

        return JsonResponse({
            "status": "success",
            "message": "Pending orders status",
            "data": {
                "has_pending_order": bool(has_pending_order)
            }
        })


class CurrentStock(View):

    def get(self, request):
        """ Get current stock """

        current_stock, created = models.StoreStatus.objects.get_or_create(
            key='current_stock'
        )
        if created:
            current_stock.value = "0"
            current_stock.save()
        current_stock_int = int(current_stock.value)

        return JsonResponse({
            "status": "success",
            "message": "Current stock",
            "data": {
                "current_stock": current_stock_int
            }
        })
