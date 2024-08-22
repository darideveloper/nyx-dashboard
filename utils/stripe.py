import requests
from django.conf import settings


def get_stripe_link(product_name: str, total: float,
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
        "url": f"{settings.LANDING_HOST}/?sale={sale_id}",
        "products": products,
        "email": email,
    }
    
    res = requests.post(settings.STRIPE_API_HOST, json=request_json)
    res.raise_for_status()
    res_data = res.json()
    
    return res_data["stripe_url"]