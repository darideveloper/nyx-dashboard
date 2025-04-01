import stripe
import requests

from django.conf import settings

from store.models import Sale, SaleStatus


def get_payment_link(product_name: str, total: float,
                    description: str, email: str, sale_id: str) -> dict:
    """ Send data to stripe api and return stripe url

    Args:
        product_name (str): product
        total (float): order total
        description (str): order description
        email (str): user email
        sale_id (str): sale id from models
        
    Returns:
        str: stripe checkout link
    """
    
    products = {}
    products[product_name] = {
        "amount": 1,
        "image_url": "https://www.nyxtrackers.com/logo.png",
        "price": total,
        "description": description
    }
    
    request_json = {
        "user": settings.STRIPE_API_USER,
        "url": f"{settings.LANDING_HOST}/",
        "url_success": f"{settings.HOST}/api/store/sale-done/{sale_id}",
        "products": products,
        "email": email,
    }
    
    res = requests.post(settings.STRIPE_API_HOST, json=request_json)
    res.raise_for_status()
    res_data = res.json()
    
    return res_data["stripe_url"]


def get_payment_link_sale(sale: Sale):
    """ Send data to stripe api and return stripe url
        using sale object
        
    Args:
        sale (Sale): sale object
        
    Returns:
        str: stripe checkout link
    """
    
    product_name = f"Tracker {sale.set.name} {sale.colors_num.num} colors"
    description = ""
    description += f"Set: {sale.set.name} | "
    description += f"Colors: {sale.colors_num.num} | "
    description += f"Client Email: {sale.user.email} | "
    description += f"Client Full Name: {sale.full_name} | "
    
    payment_link = get_payment_link(
        product_name=product_name,
        total=sale.total,
        description=description,
        email=sale.user.email,
        sale_id=sale.id
    )
    
    return payment_link


def update_transaction_link(sale: Sale) -> bool:
    """ Get last sale of specific amount and client
    
    Args:
        sale (Sale): sale object
        
    Returns:
        bool: True if payment found, False otherwise
    """
    
    payment_found = False
    
    # Set stripe api key
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Get last payments
    charges = stripe.Charge.list(status="succeeded", limit=100)
    if not charges['data']:
        sale.payment_link = "No payments found in this stripe account"
    
    # Get client payments
    client_charges = []
    for charge in charges['data']:
        if charge['billing_details']['email'] == sale.user.email:
            print(charge['billing_details']['email'], sale.user.email)
            client_charges.append(charge)
        
    # Filter payments by amount
    for charge in client_charges:
        if charge['amount'] == sale.total * 100:
            payment_id = charge['id']
            sale.payment_link = f"https://dashboard.stripe.com/payments/{payment_id}"
            payment_found = True
            
    # Return error
    if not payment_found:
        sale.payment_link = "No payment found with this amount for this client"
   
    # Add staus and save sale
    if payment_found:
        status = SaleStatus.objects.get(value="Paid")
    else:
        status = SaleStatus.objects.get(value="Payment Error")
    sale.status = status
    sale.save()
    
    return payment_found