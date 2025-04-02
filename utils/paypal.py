from time import sleep

import requests
from django.conf import settings


class PaypalCheckout:

    def __init__(self):
        """Setup global data"""

        access_token = self.__get_access_token__()
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

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
    
    def capture_payment(self, order_id: str) -> dict:
        """Capture the payment from PayPal"""
        capture_url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
        
        response = requests.post(
            capture_url,
            headers=self.headers,
        )

        capture_data = response.json()
        response.raise_for_status()
        return capture_data

    def get_checkout_link(
        self,
        sale_id: str,
        title: str,
        price: str,
        description: str,
    ) -> dict:
        """Get PayPal Checkout URL

        Args:
            sale_id (str): Sale ID from models
            title (str): Product title
            price (str): Product price
            description (str): Product description

        Returns:
            dict: PayPal Checkout URLs
                {
                    "payer-action": payment link
                    "self": checkout details endpoint
                }
        """

        error_page = f"{settings.LANDING_HOST}/?sale-status=error&sale-id={sale_id}"
        success_page = f"{settings.HOST}/api/store/sale-done/{sale_id}/"

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
                        "locale": "en-US",
                        "shipping_preference": "NO_SHIPPING",
                        "return_url": success_page,
                        "cancel_url": error_page,
                        "landing_page": "GUEST_CHECKOUT",
                    },
                },
            },
        }

        order = {}
        for _ in range(3):
            try:
                response = requests.post(
                    f"{settings.PAYPAL_API_BASE}/v2/checkout/orders",
                    json=order_data,
                    headers=self.headers,
                )
                order = response.json()
                response.raise_for_status()
            except Exception as e:
                print(f"Error generating PayPal checkout link: {e}. Retrying...")
                sleep(10)
                continue
            else:
                break

        if not order:
            raise Exception("PayPal checkout link generation failed")

        # Get links from order response
        links_data = {
            "payer-action": "",
            "self": "",
        }

        for link in order["links"]:
            if link["rel"] in links_data.keys():
                link_name = link["rel"]
                links_data[link_name] = link["href"]

        return links_data
    
    def is_payment_done(
        self, order_details_link: str, use_testing: bool = False
    ) -> bool:
        """Check if payment is done

        Args:
            order_details_link (str): PayPal Order Details Link
            use_testing (bool): Use testing mode (default: False)

        Returns:
            bool: True if payment is done, False otherwise
        """

        try:
            response = requests.get(
                order_details_link,
                headers=self.headers,
            )

            json_data = response.json()
            status = json_data["status"]
            
            if status == "APPROVED":
                self.capture_payment(json_data["id"])  # Capture the payment
                return True

            return status == "COMPLETED" or (use_testing and settings.IS_TESTING)
            
        except Exception as e:
            print(f"Error checking payment status: {e}")
            return False
