from django.conf import settings
from utils.stripe import StripeCheckout
from utils.paypal import PaypalCheckout


def get_payment_provider(sale=None):
    if sale and sale.payment_link:
        if sale.payment_link.startswith("cs_"):
            return StripeCheckout()
        elif sale.payment_link.startswith("http"):
            return PaypalCheckout()

    provider = settings.PAYMENT_PROVIDER
    if provider == "stripe":
        return StripeCheckout()
    return PaypalCheckout()
