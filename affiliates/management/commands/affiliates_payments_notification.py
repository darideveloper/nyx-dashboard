from django.conf import settings
from django.core.management.base import BaseCommand

from affiliates.models import Affiliate
from utils.emails import send_email


class Command(BaseCommand):
    help = 'Submit payment notifications to admin about '
    help += 'affiliates with positive balances.'
    
    def handle(self, *args, **kwargs):

        # Send email for each affiliate
        affiliates = Affiliate.objects.all().order_by('id')
        for affiliate in affiliates:
            
            # Skip if the affiliate is not active
            if not affiliate.user.is_active:
                print(f"Affiliate {affiliate.name} is not active. Skipping...")
                continue
            
            # Skip if the affiliate has no balance
            if affiliate.balance <= 0:
                print(f"Affiliate {affiliate.name} has no balance. Skipping...")
                continue
            
            # Send email to admin
            print(f"Sending email to admin for affiliate {affiliate.name}...")
            cta_link = f"{settings.HOST}/admin/affiliates/payment/add/"
            cta_link += f"?amount={affiliate.balance}"
            cta_link += f"&affiliate={affiliate.id}"
            cta_link += "&status=COMPLETED"
            
            send_email(
                subject=f"Payment Notification for {affiliate.name}",
                first_name="Admin",
                last_name="",
                texts=[
                    "Here a payment that should be sent to the affiliate",
                    f"Affiliate ID: {affiliate.id}",
                    f"Affiliate Name: {affiliate.name}",
                    f"Affiliate Email: {affiliate.email}",
                    f"Amount to be paid: {affiliate.balance}",
                    "Please review the payment details and proceed accordingly.",
                ],
                cta_link=cta_link,
                cta_text="Review Payment",
                to_email=settings.ADMIN_EMAIL
            )
            
            print(f"Email sent to admin for affiliate {affiliate.name}")