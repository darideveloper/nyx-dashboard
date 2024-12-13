import logging

from django.core.management.base import BaseCommand

from store import models
from utils.stripe import update_transaction_link

logger = logging.getLogger()


class Command(BaseCommand):
    help = 'update all stripe links of successful sales in dahsboard'
    
    def handle(self, *args, **kwargs):
        sales = models.Sale.objects.filter(status__value='Paid')
        logger.info(f"{sales.count()} sales to update")
        
        for sale in sales:
            update_transaction_link(sale)
            logger.info(f"Sale {sale} updated: {sale.stripe_link}")