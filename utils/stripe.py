import requests

from django.conf import settings

from store.models import Sale


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
        "url": f"{settings.LANDING_HOST}/",
        "url_success": f"{settings.HOST}/api/store/sale-done/{sale_id}",
        "products": products,
        "email": email,
    }
    
    res = requests.post(settings.STRIPE_API_HOST, json=request_json)
    res.raise_for_status()
    res_data = res.json()
    
    return res_data["stripe_url"]


def get_stripe_link_sale(sale: Sale):
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
    
    stripe_link = get_stripe_link(
        product_name=product_name,
        total=sale.total,
        description=description,
        email=sale.user.email,
        sale_id=sale.id
    )
    
    return stripe_link
    