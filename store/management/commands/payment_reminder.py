import os

from django.core.management.base import BaseCommand

from store import models
from utils.emails import send_email
from utils.stripe import get_stripe_link_sale

BASE_FILE = os.path.basename(__file__)


class Command(BaseCommand):
    help = 'Send payment reminder to users after 1 days'
    
    def handle(self, *args, **kwargs):
        # Get payments from yesterday
        pending_status, _ = models.SaleStatus.objects.get_or_create(value='Pending')
        sales = models.Sale.objects.filter(
            status=pending_status,
        )
        
        print(f"{BASE_FILE}: {sales.count()} sales to remind")
        
        for sale in sales:
            
            # Generate new stripe link
            stripe_link = get_stripe_link_sale(sale)
                        
            # Send email
            send_email(
                subject="Don't forget to pay for your order!",
                first_name=sale.user.first_name,
                last_name=sale.user.last_name,
                texts=[
                    "You have an order pending payment.",
                    "Please pay as soon as possible."
                ],
                cta_link=stripe_link,
                cta_text="Pay now",
                to_email=sale.user.email
            )
            
            print(f"{BASE_FILE}: Reminder sent to {sale.user.email} in sale {sale.id}")
            
            # Update status
            remainder_sent_status, _ = models.SaleStatus.objects.get_or_create(
                value='Reminder Sent'
            )
            sale.status = remainder_sent_status
            sale.save()
            print(f"{BASE_FILE}: Status updated to {sale.status} in sale {sale.id}")