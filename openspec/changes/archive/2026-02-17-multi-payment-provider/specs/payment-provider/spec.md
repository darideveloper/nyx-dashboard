# Payment Provider Specification

This spec covers the implementation details for supporting both PayPal and Stripe.

## ADDED Requirements

### Requirement: Environment-Based Switching
The system MUST read `PAYMENT_PROVIDER` from environment variables to determine the active provider for **new sales**.

#### Scenario: Verify Provider Selection
```python
# nyx_dashboard/settings.py
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "paypal")

# store/views.py
from utils.paypal import PaypalCheckout
from utils.stripe import StripeCheckout

def get_payment_provider(sale=None):
    if sale and sale.payment_link:
        if sale.payment_link.startswith("cs_"):
            return StripeCheckout()
        elif sale.payment_link.startswith("http"):
            return PaypalCheckout()
            
    if settings.PAYMENT_PROVIDER == "stripe":
        return StripeCheckout()
    return PaypalCheckout()
```

### Requirement: Stripe Checkout Integration
The `StripeCheckout` class MUST implement the `get_checkout_link` method using `stripe.checkout.Session.create`.

#### Scenario: Generate Checkout Link (Stripe)
```python
# utils/stripe.py
class StripeCheckout:
    def get_checkout_link(self, sale_id, title, price, description):
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': title},
                    'unit_amount': int(price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{settings.HOST}/api/store/sale-done/{sale_id}",
            cancel_url=f"{settings.LANDING_HOST}/?sale-status=error&sale-id={sale_id}",
            metadata={'sale_id': sale_id}
        )
        return {
            "payer-action": session.url,
            "self": session.id 
        }
```

### Requirement: Stripe Payment Verification
The `StripeCheckout` class MUST verify payment status by retrieving the checkout session.

#### Scenario: Verify Payment (Stripe)
```python
# utils/stripe.py
class StripeCheckout:
    def is_payment_done(self, payment_identifier, use_testing=False, sale_id=None):
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        try:
            session = stripe.checkout.Session.retrieve(payment_identifier)
            return session.payment_status == 'paid'
        except stripe.error.StripeError:
            return False
        except Exception:
            return False
```

### Requirement: Provider Factory Usage
All payment-related views MUST use the `get_payment_provider` factory instead of direct class instantiation to ensure provider-agnostic processing.

#### Scenario: Using the Factory
```python
# store/views.py
provider = get_payment_provider(sale)
links = provider.get_checkout_link(...)
```

