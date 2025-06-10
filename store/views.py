import re
import os
import json
import base64
import locale
from pathlib import Path

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
from utils.pdf_generator import generate_pdf
from utils.paypal import PaypalCheckout
from affiliates.models import Affiliate
from store.models import StoreStatus

from dotenv import load_dotenv


class NextFutureStock(View):

    def get(self, request, email=""):
        """Return next future stock datetime

        Args:
            request (HttpRequest): Django request object
            email (str): User email to check if already subscribed
        """

        future_stock = (
            models.FutureStock.objects.filter(added=False).order_by("datetime").first()
        )
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
                user=user, future_stock=future_stock, active=True
            ).exists()

        return JsonResponse(
            {
                "next_future_stock": next_future_stock_seconds,
                "already_subscribed": already_subscribed,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class FutureStockSubscription(View):

    def post(self, request):
        """Subscribe to future stock"""

        # Get json data
        json_data = json.loads(request.body)
        subscription_email = json_data.get("email")
        subscription_type = json_data.get("type")

        # Validate susbcription type
        if subscription_type not in ["add", "remove"]:
            return JsonResponse({"message": "Invalid subscription type"}, status=400)

        # Get or create auth user
        users = models.User.objects.filter(email=subscription_email)
        if users:
            user = users[0]
        else:
            user = models.User.objects.create(
                email=subscription_email, username=subscription_email
            )

        # Get and validate future stock
        future_stock = models.FutureStock.objects.filter(added=False)
        if not future_stock:
            return JsonResponse({"message": "Future stock not found"}, status=404)
        future_stock = future_stock[0]

        # Validate if user is already subscribed
        current_subscription = models.FutureStockSubscription.objects.filter(
            user=user, future_stock=future_stock
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
                    user=user, future_stock=future_stock
                )
            return JsonResponse({"message": "Subscribed to future stock"})
        else:
            # Deactivate subscription
            subscription = models.FutureStockSubscription.objects.filter(
                user=user, future_stock=future_stock
            )
            if not subscription:
                return JsonResponse({"message": "Subscription not found"}, status=404)
            subscription = subscription[0]
            subscription.active = False
            subscription.save()

            return JsonResponse({"message": "Unsubscribed from future stock"})


@method_decorator(csrf_exempt, name="dispatch")
class Sale(View):

    def post(self, request):
        """Sale sale from landing"""

        # Get json data
        json_data = json.loads(request.body)

        # Validate required fields
        required_fields = [
            "email",
            "set",
            "colors_num",
            "logo",
            "included_extras",
            "promo",
            "full_name",
            "country",
            "state",
            "city",
            "postal_code",
            "street_address",
            "phone",
        ]
        for field in required_fields:
            if field not in json_data:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Missing field: {field}",
                        "data": {},
                    },
                    status=400,
                )

        # Get info
        email = json_data["email"]
        set = json_data["set"]
        colors_num = json_data["colors_num"]
        logo_base64 = json_data["logo"]
        addons = json_data["included_extras"]
        promo = json_data["promo"]
        full_name = json_data["full_name"]
        country = json_data["country"]
        state = json_data["state"]
        city = json_data["city"]
        postal_code = json_data["postal_code"]
        street_address = json_data["street_address"]
        phone = json_data["phone"]
        comments = json_data.get("comments", "")

        # Generate colors instances
        colors = {
            "color_set": json_data["set_color"],
            "logo_color_1": json_data["logo_color_1"],
            "logo_color_2": json_data["logo_color_2"],
            "logo_color_3": json_data["logo_color_3"],
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
                " orders in one place and in real time.",
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

        try:
            promo_type = promo["discount"]["type"]
            promo_value = promo["discount"]["value"]
            promo_type_obj = models.PromoCodeType.objects.get(name=promo_type)

            promo_obj = models.PromoCode.objects.filter(
                code=promo["code"],
                discount=promo_value,
                type=promo_type_obj,
            )
            promo_obj = promo_obj[0]
        except Exception:
            promo_obj = None

        # Calculate total
        total = 0
        total += set_obj.price
        total += colors_num_obj.price
        for addon in addons_objs:
            total += addon.price
        if promo_obj:
            if promo_obj.type.name == "percentage":
                total -= total * promo_obj.discount / 100
            else:
                total -= promo_obj.discount
        total = round(total, 2)

        # Get status
        status = models.SaleStatus.objects.get(value="Pending")

        # Validate if user has a pending order
        pending_sales = models.Sale.objects.filter(user=user, status__value="Pending")

        # Delete old pending sales
        if bool(pending_sales):

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
                    f"The sale has been updated by the user {user.email}.",
                    "Check the sale in the dashboard.",
                ],
                cta_link=f"{settings.HOST}/admin/store/sale/"
                f"?user__id__exact={user.id}",
                cta_text="View sale in dashboard",
                to_email=settings.ADMIN_EMAIL,
            )

        # Create new sale
        sale = models.Sale.objects.create(
            user=user,
            set=set_obj,
            colors_num=colors_num_obj,
            color_set=colors_instances["color_set"],
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

        # Add extra colors
        if colors_num >= 2:
            sale.logo_color_1 = colors_instances["logo_color_1"]
        if colors_num >= 3:
            sale.logo_color_2 = colors_instances["logo_color_2"]
        if colors_num == 4:
            sale.logo_color_3 = colors_instances["logo_color_3"]
        sale.save()

        # Set addons
        sale.addons.clear()
        sale.addons.set(addons_objs)

        # get image file in base64 and save
        try:
            if logo_base64:

                # Validate logo format
                match = re.match(r"data:image/(png|svg\+xml);base64,(.*)", logo_base64)
                if not match:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Invalid logo format",
                            "data": {},
                        },
                        status=400,
                    )

                # Get logo parts
                logo_file_type = match.group(1)
                logo_base64_string = match.group(2)
                if logo_file_type == "svg+xml":
                    logo_file_type = "svg"
                logo_data = base64.b64decode(logo_base64_string)

                # Create a file name
                file_name = f"sale_{sale.id}_logo.{logo_file_type}"

                # Save the logo file
                sale.logo.save(file_name, ContentFile(logo_data))
        except Exception:

            # Delete sale
            sale.delete()

            # Error response
            return JsonResponse(
                {"status": "error", "message": "Error saving logo", "data": {}},
                status=400,
            )

        # get payment link
        paypal_checkout = PaypalCheckout()
        links = paypal_checkout.get_checkout_link(
            sale_id=sale.id,
            title=f"Tracker {sale.set.name} {sale.colors_num.num} colors",
            price=sale.total,
            description=f"Set: {sale.set.name} | Colors: {sale.colors_num.num}",
        )

        # Save order details endpoint in sale
        sale.payment_link = links["self"]
        sale.save()

        # Validate stock
        current_stock = models.StoreStatus.objects.filter(key="current_stock").first()
        current_stock_value = int(current_stock.value) if current_stock else 0
        if current_stock_value <= 0:
            return JsonResponse(
                {"status": "error", "message": "No stock available", "data": {}},
                status=400,
            )

        return JsonResponse(
            {
                "status": "success",
                "message": "Sale saved",
                "data": {
                    "payment_link": links["payer-action"],
                },
            }
        )


class SaleDone(View):

    def get(self, request, sale_id: str):
        """Update sale status and redirect to landing

        Args:
            request (HttpRequest): Django request object
            sale_id (str): sale id from url
        """

        # Get "testing" from get params
        use_testing = request.GET.get("use_testing", False)

        # Landing page links
        landing_done_page = settings.LANDING_HOST
        landing_error_page = landing_done_page + f"?sale-id={sale_id}&sale-status=error"

        # Check if sale exists
        sales = models.Sale.objects.filter(id=sale_id)
        if not sales:
            return redirect(landing_error_page)
        sale = sales[0]

        # Validate payment in paypal
        paypal_checkout = PaypalCheckout()
        payment_done = paypal_checkout.is_payment_done(
            sale.payment_link,
            use_testing,
            sale.id,
        )
        sale.refresh_from_db()
        if not payment_done:

            # Send error email to client
            email_texts = [
                "There was an error with your payment.",
                "Your order has not been processed.",
                "Please try again or contact us for support.",
            ]

            send_email(
                subject="Nyx Trackers Payment Error",
                first_name=sale.user.first_name,
                last_name=sale.user.last_name,
                texts=email_texts,
                cta_link=f"{settings.HOST}/admin/",
                cta_text="Visit dashboard",
                to_email=sale.user.email,
            )

            # Redirect to landing with error
            return redirect(landing_error_page)

        # Update payment link in sale
        sale.status = models.SaleStatus.objects.get(value="Paid")
        sale.save()

        # Update stock
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock_int = int(current_stock.value)
        current_stock.value = str(current_stock_int - 1)
        current_stock.save()

        # Get sale data
        sale_data = sale.get_sale_data_dict()

        # Build paths inside the project like this: BASE_DIR / 'subdir'.
        BASE_DIR = Path(__file__).resolve().parent.parent

        # Setup .env file
        load_dotenv()
        ENV = os.getenv('ENV')
        env_path = os.path.join(BASE_DIR, f'.env.{ENV}')
        load_dotenv(env_path)

        igi_comission = os.getenv('IGI')
        paypal_comission = os.getenv('PAYPAL')
        igi = float(sale_data["Total"]) * float(igi_comission) / 100
        paypal = float(sale_data["Total"]) * float(paypal_comission) / 100
        base = float(sale_data["Total"]) - igi - paypal

        invoice_num = StoreStatus.objects.filter(key="invoice_num").first()

        # Format date
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  
        
        date = timezone.now()
        format_date = date.strftime('%d de %B de %Y')

        # Generate PDF
        generate_pdf(
            invoice=invoice_num.value,
            date=str(format_date),
            name=sale_data["Full Name"],
            city=sale_data["City"],
            state=sale_data["State"],
            street=sale_data["Street Address"],
            pc=sale_data["Postal Code"],
            country=sale_data["Country"],
            phone=sale_data["Phone"],
            email=sale_data["Email"],
            quantity="1",
            base=str(round(base,2)),
            igi=str(round(igi,2)),
            paypal=str(round(paypal,2)),
            total=str(round(sale_data["Total"],2))
        )

        invoice_num.value = str(int(invoice_num.value) + 1)
        invoice_num.save()

        email_texts = [
            "Your payment has been confirmed!",
            "Your order is being processed.",
            "You will receive notifications about the status of your order.",
            "Here your order details:",
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
            image_src=logo_url,
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
            image_src=logo_url,
        )

        # Update balance in affiliate program
        promo_code = sale.promo_code
        affiliates = Affiliate.objects.filter(promo_code=promo_code)
        if affiliates:
            affiliate = affiliates[0]
            affiliate.balance += (
                int(sale.total * settings.AFFILIATES_COMMISSION * 100) / 100
            )
            affiliate.save()

        # Redirect to landing
        landing_done_page += f"?sale-id={sale_id}&sale-status=success"
        return redirect(landing_done_page)


@method_decorator(csrf_exempt, name="dispatch")
class PromoCode(View):

    def post(self, request):
        """Validate promo code"""

        # Get promo code value form json data
        json_data = json.loads(request.body)
        promo_code = json_data.get("promo_code")

        # Check if promo code exists
        promo = models.PromoCode.objects.filter(code=promo_code)
        if not promo:
            return JsonResponse(
                {"status": "error", "message": "Invalid promo code", "data": {}},
                status=404,
            )

        promo = promo[0]

        # Return promo count discount and type
        return JsonResponse(
            {
                "status": "success",
                "message": "Valid promo code",
                "data": {
                    "value": promo.discount,
                    "type": promo.type.name,
                },
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class PendingOder(View):

    def post(self, request):
        """Check if user has pending orders"""

        # Get user's email from json
        json_data = json.loads(request.body)
        email = json_data.get("email")

        # Get user
        user = models.User.objects.filter(email=email)

        # Validate user and Check if user has pending orders
        has_pending_order = None
        if user:
            user = user[0]
            has_pending_order = models.Sale.objects.filter(
                user=user, status__value="Pending"
            )

        return JsonResponse(
            {
                "status": "success",
                "message": "Pending orders status",
                "data": {"has_pending_order": bool(has_pending_order)},
            }
        )


class CurrentStock(View):

    def get(self, request):
        """Get current stock"""

        current_stock, created = models.StoreStatus.objects.get_or_create(
            key="current_stock"
        )
        if created:
            current_stock.value = "0"
            current_stock.save()
        current_stock_int = int(current_stock.value)

        return JsonResponse(
            {
                "status": "success",
                "message": "Current stock",
                "data": {"current_stock": current_stock_int},
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class PaymentLink(View):

    def get(self, request, sale_id: str):
        """Get new payment payment link for sale"""

        landing_done_page = settings.LANDING_HOST
        landing_error_page = landing_done_page + f"?sale-id={sale_id}&sale-status=error"

        # Get sale
        sales = models.Sale.objects.filter(id=sale_id)
        if not sales:
            return redirect(landing_error_page)
        sale = sales[0]

        # Get payment link
        paypal_checkout = PaypalCheckout()
        links = paypal_checkout.get_checkout_link(
            sale_id=sale.id,
            title=f"Tracker {sale.set.name} {sale.colors_num.num} colors",
            price=sale.total,
            description=f"Set: {sale.set.name} | Colors: {sale.colors_num.num}",
        )

        # Save order details endpoint in sale
        sale.payment_link = links["self"]
        sale.save()

        # Redirect to payment link
        return redirect(links["payer-action"])
