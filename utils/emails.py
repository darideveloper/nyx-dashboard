import os

import requests

from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def render_email(first_name: str, last_name: str,
                 texts: list[str], cta_link: str, cta_text: str,
                 key_items: dict = {}, extra_image: bool = False) -> tuple[str, str]:
    """ Send an email to the user to activate their account.

    Args:
        first_name (str): user first name
        last_name (str): user last name
        texts (list[str]): list of strings to display above the CTA
        cta_link (str): link to the CTA
        cta_text (str): text to display on the CTA
        key_items (dict): list items like key-value pairs to display in the email
        extra_image (bool): if an extra image is provided in the email
        
    Returns:
        tuple[str, str]: html_message, plain_message
        
    """
    
    # Rende html content
    context = {
        "first_name": first_name,
        "last_name": last_name,
        "texts": texts,
        "cta_link": cta_link,
        "cta_text": cta_text,
        "key_items": key_items,
        "extra_image": extra_image
    }
    
    html_message = render_to_string('user/email.html', context)
    plain_message = strip_tags(html_message)
    
    return html_message, plain_message
    
    
def send_email(subject: str, first_name: str, last_name: str,
               texts: list[str], cta_link: str, cta_text: str,
               to_email: str, key_items: dict = {}, image_src: str = ""):
    """ Send an email to the user to activate their account.

    Args:
        subject (str): email subject (title
        first_name (str): user first name
        last_name (str): user last name
        texts (list[str]): list of strings to display above the CTA
        cta_link (str): link to the CTA
        cta_text (str): text to display on the CTA
        to_email (str): email to send the email to
        key_items (dict): list items like key-value pairs to display in the email
        image_src (str): extra image source to display in the email
    """
    
    # Get rendered html
    html_message, plain_message = render_email(
        first_name,
        last_name,
        texts,
        cta_link,
        cta_text,
        key_items,
        extra_image=image_src != ""
    )
    
    # Add html and plain text to the email
    message = EmailMultiAlternatives(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [to_email]
    )
    message.attach_alternative(html_message, "text/html")
    
    if image_src:
        # Download image in a temp folder
        image_base = image_src.split("/")[-1]
        image_temp_folder = os.path.join(settings.BASE_DIR, "media", "temp")
        image_temp_path = f"{image_temp_folder}/{image_base}"
        os.makedirs(image_temp_folder, exist_ok=True)
        
        try:
            res = requests.get(image_src)
        except Exception:
            pass
        else:
            with open(image_temp_path, 'wb') as img:
                img.write(res.content)
            
            # Attach an image if provided
            with open(image_temp_path, 'rb') as img:
                img_data = img.read()
            image = MIMEImage(img_data, name=image_base)
            image.add_header('Content-ID', '<image1>')
            message.attach(image)
    
    message.send()