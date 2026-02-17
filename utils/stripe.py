import stripe
from django.conf import settings
from store.models import Sale


class StripeCheckout:

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def get_checkout_link(
        self,
        sale_id: str,
        title: str,
        price: float,
        description: str,
    ) -> dict:
        """Get Stripe Checkout URL

        Args:
            sale_id (str): Sale ID from models
            title (str): Product title
            price (float): Product price
            description (str): Product description

        Returns:
            dict: Stripe Checkout URLs
                {
                    "payer-action": payment link
                    "self": session id
                }
        """

        # Convert price to cents
        amount = int(float(price) * 100)

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": title,
                                "description": description,
                            },
                            "unit_amount": amount,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{settings.HOST}/api/store/sale-done/{sale_id}/",
                cancel_url=f"{settings.LANDING_HOST}/?sale-status=error&sale-id={sale_id}",
                client_reference_id=sale_id,
                metadata={
                    "sale_id": sale_id,
                },
            )

            return {
                "payer-action": session.url,
                "self": session.id,
            }
        except Exception as e:
            print(f"Error generating Stripe checkout link: {e}")
            raise e

    def is_payment_done(self, sale, use_testing: bool = False) -> bool:
        """Check if payment is done

        Args:
            sale (Sale): Sale object
            use_testing (bool): Use testing mode (default: False)

        Returns:
            bool: True if payment is done, False otherwise
        """

        # Simulate payment done in testing mode
        if use_testing and settings.IS_TESTING:
            return True

        session_id = sale.payment_link
        if not session_id or not session_id.startswith("cs_"):
            return False

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                return True
            return False
        except Exception as e:
            print(f"Error validating Stripe payment: {e}")
            return False
