import requests
from django.conf import settings


class PaypalCheckout:

    def __get_access_token__(self) -> str:
        """Get PayPal OAuth2 Access Token

        Returns:
            str: PayPal OAuth2 Access Token
        """
        auth_response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={
                "Accept": "application/json",
                "Accept-Language": "en_US",
            },
        )

        auth_response.raise_for_status()
        return auth_response.json()["access_token"]

    def get_checkout_link(
        self,
        sale_id: str,
        title: str,
        price: str,
        description: str,
        image_url: str,
    ) -> str:
        """Get PayPal Checkout URL

        Args:
            sale_id (str): Sale ID from models
            title (str): Product title
            price (str): Product price
            description (str): Product description
            image_url (str): Product image URL

        Returns:
            str: PayPal Checkout URL
        """

        access_token = self.__get_access_token__()
        
        error_page = f"{settings.LANDING_HOST}/?sale-status=error&sale-id={sale_id}"
        success_page = f"{settings.HOST}/sale-done/{sale_id}/"

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": sale_id,
                    "description": description,
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{price:.2f}",
                        "breakdown": {
                            "item_total": {
                                "currency_code": "USD",
                                "value": f"{price:.2f}",
                            }
                        },
                    },
                    "items": [
                        {
                            "name": title,
                            "description": description,
                            "unit_amount": {
                                "currency_code": "USD",
                                "value": f"{price:.2f}",
                            },
                            "quantity": "1",
                            "category": "DIGITAL_GOODS",
                            "image_url": image_url,
                        }
                    ],
                }
            ],
            "payment_source": {
                "paypal": {
                    # # Auto fill data for new paypal users
                    # "name": {"given_name": "Firstname", "surname": "Lastname"},
                    # "address": {
                    #     "address_line_1": "TEST C",
                    #     "address_line_2": "TEST B",
                    #     "admin_area_2": "TEST A",
                    #     "admin_area_1": "CATAMARCA",
                    #     "postal_code": "20010",
                    #     "country_code": "AR",
                    # },
                    "experience_context": {
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                        "brand_name": "Darideveloper",
                        "locale": "en-US",
                        "shipping_preference": "NO_SHIPPING",
                        "return_url": success_page,
                        "cancel_url": error_page,
                        "landing_page": "GUEST_CHECKOUT",
                    },
                },
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.post(
            f"{settings.PAYPAL_API_BASE}/v2/checkout/orders",
            json=order_data,
            headers=headers,
        )
        order = response.json()
        print(order)
        response.raise_for_status()

        checkout_link = next(
            link["href"] for link in order["links"] if link["rel"] == "payer-action"
        )

        return checkout_link


# Example usage
paypal_checkout = PaypalCheckout()
checkout_url = paypal_checkout.get_checkout_link(
    title="Cool Product",
    price=19.99,
    description="This is an awesome product!",
    image_url="https://www.darideveloper.com/imgs/logo.png",
    sale_id=99,
)

print(">>>>>>>>>>> PayPal Checkout URL:", checkout_url)
