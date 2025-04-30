import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from store import models
from utils.emails import send_email

logger = logging.getLogger()


class Command(BaseCommand):
    help = 'Send payment reminder to users after 1 days'
    
    def handle(self, *args, **kwargs):
        # Get payments in "Pending" or "Reminder Sent" status
        pending_status = models.SaleStatus.objects.get(value='Pending')
        reminder_sent_status = models.SaleStatus.objects.get(value='Reminder Sent')
        sales = models.Sale.objects.filter(
            status__in=[pending_status, reminder_sent_status],
            reminders_sent__lt=3
        )
        
        logger.info(f"{sales.count()} sales to remind")
        
        for sale in sales:
                        
            # 15% of discount to sale if its 3rd reminder
            is_discount = False
            if sale.reminders_sent == 2:
                is_discount = True
                sale.total = sale.total * 0.85
                logger.info(f"promo price applied to sale '{sale.id}'")
            
            # generate payment link
            payment_link = settings.HOST + f"/api/store/payment-link/{sale.id}/"
            
            subject = "Don't forget to pay for your order!"
            texts = [
                "You have an order pending payment.",
                "You are one step away from getting your dream Fbt!"
                " Click here to finish the process."
            ]
            cta_text = "Pay now"
            if is_discount:
                subject += " - 15% discount"
                texts.append("Just for you, we are offering a 15%"
                             " discount on your order.")
                cta_text += " with 15% discount"
                        
            # Send email
            send_email(
                subject=subject,
                first_name=sale.user.first_name,
                last_name=sale.user.last_name,
                texts=texts,
                cta_link=payment_link,
                cta_text=cta_text,
                to_email=sale.user.email
            )
            
            message = f"Reminder sent to '{sale.user.email}' in sale '{sale.id}'"
            logger.info(message)
            
            # Update status
            remainder_sent_status, _ = models.SaleStatus.objects.get_or_create(
                value='Reminder Sent'
            )
            sale.status = remainder_sent_status
            sale.reminders_sent += 1
            sale.save()
            logger.info(f"Sale '{sale.id}' updated")