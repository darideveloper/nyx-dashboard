import os
from dotenv import load_dotenv
from store import models
from django.core.management.base import BaseCommand
from django.utils import timezone
from utils.emails import send_email

# Env variables
load_dotenv()
LANDING_HOST = os.getenv("LANDING_HOST")

BASE_FILE = os.path.basename(__file__)


class Command(BaseCommand):
    help = 'Update stock when future stock datetime is reached'

    def handle(self, *args, **kwargs):
        # Get future stocks to save
        now = timezone.now()
        future_stoks = models.FutureStock.objects.filter(
            added=False,
            datetime__lte=now
        )
        print(f"{BASE_FILE}: {future_stoks.count()} future stocks to add")
        
        for future_stock in future_stoks:
            
            # Update future stock status
            future_stock.added = True
            future_stock.save()
            
            # Update stock in Status model
            current_stock = models.Status.objects.get(key='current_stock')
            current_stock_value = int(current_stock.value) + future_stock.amount
            current_stock.value = str(current_stock_value)
            current_stock.save()
            print(f"{BASE_FILE}: Stock updated to {current_stock_value}")
            
            # Send email to subscribers
            subscriptions = models.FutureStockSubscription.objects.filter(
                future_stock=future_stock
            )
            for subscription in subscriptions:
                
                # Send email
                send_email(
                    subject="New sets available now!",
                    first_name=subscription.user.first_name,
                    last_name=subscription.user.last_name,
                    texts=[
                        "We have added new sets to our store.",
                        "Check them out now!"
                    ],
                    cta_link=f"{LANDING_HOST}#buy-form",
                    cta_text="Buy now",
                    to_email=subscription.user.email
                )
                
                # Update status
                subscription.notified = True
                subscription.save()
                
                print(f"{BASE_FILE}: Email sent to {subscription.user.email}")