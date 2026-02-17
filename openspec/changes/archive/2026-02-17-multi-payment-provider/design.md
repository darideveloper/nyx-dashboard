# Payment Provider Design

This change implements a strategy pattern for payment processing.

## Components

### 1. Payment Provider Interface

We will define an implicit (Duck Typing) `PaymentProvider` interface that both `PaypalCheckout` and `StripeCheckout` adhere to.

```python
class PaymentProvider:
    def get_checkout_link(self, sale_id: str, title: str, price: float, description: str) -> dict:
        """
        Returns:
            dict: {
                "payer-action": str, # User redirect URL
                "self": str          # Internal ID or API link for verification
            }
        """
        pass

    def is_payment_done(self, sale: Sale, use_testing: bool = False) -> bool:
        """
        Extracts payment ID from sale.payment_link and verifies status.
        Returns:
            bool: True if payment is approved/captured.
        """
        pass
```

### 2. Provider Selection Logic

*   **New Sales**: `store.views.Sale` will use `settings.PAYMENT_PROVIDER` to instantiate the correct provider.
*   **Existing/Pending Sales**: `store.views.SaleDone` will detect the provider based on the `sale.payment_link` format:
    *   Starts with `cs_` (e.g., `cs_test_...`): Use `StripeCheckout`.
    *   Starts with `http` (PayPal uses API URLs): Use `PaypalCheckout`.
    *   As a fallback, `settings.PAYMENT_PROVIDER` can be used.

### 3. Stripe Implementation

We will rewrite `utils/stripe.py` to use `stripe.checkout.Session`. The key differences:
*   `stripe.checkout.Session.create` returns a session object.
*   `session.url` corresponds to `payer-action`.
*   `session.id` corresponds to `self`.

This avoids database migrations by repurposing `sale.payment_link` to store the unique payment identifier for both systems.
