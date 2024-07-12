from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator


def get_selenium_elems(driver: webdriver, selectors: dict) -> dict[str, WebElement]:
    fields = {}
    for key, value in selectors.items():
        fields[key] = driver.find_element(By.CSS_SELECTOR, value)
    return fields


def render_email(first_name: str, last_name: str,
                 texts: list[str], cta_link: str, cta_text: str) -> tuple[str, str]:
    """ Send an email to the user to activate their account.

    Args:
        first_name (str): user first name
        last_name (str): user last name
        texts (list[str]): list of strings to display above the CTA
        cta_link (str): link to the CTA
        cta_text (str): text to display on the CTA
        
    Returns:
        tuple[str, str]: html_message, plain_message
        
    """
    
    # Rende html content
    context = {
        "first_name": first_name,
        "last_name": last_name,
        "texts": texts,
        "cta_link": cta_link,
        "cta_text": cta_text
    }
    
    html_message = render_to_string('user/email.html', context)
    plain_message = strip_tags(html_message)
    
    return html_message, plain_message
    
    
def send_email(subject: str, first_name: str, last_name: str,
               texts: list[str], cta_link: str, cta_text: str,
               to_email: str):
    """ Send an email to the user to activate their account.

    Args:
        subject (str): email subject (title
        first_name (str): user first name
        last_name (str): user last name
        texts (list[str]): list of strings to display above the CTA
        cta_link (str): link to the CTA
        cta_text (str): text to display on the CTA
        to_email (str): email to send the email to
    """
    
    html_message, plain_message = render_email(
        first_name,
        last_name,
        texts,
        cta_link,
        cta_text
    )
    
    message = EmailMultiAlternatives(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [to_email]
    )
    message.attach_alternative(html_message, "text/html")
    message.send()
    
    
def get_id_token(user: User):
    """ Return the id and token of a user.

    Args:
        user (User): user to get the id and token from
    """
    
    token_manager = PasswordResetTokenGenerator()
    token = token_manager.make_token(user)
    return f"{user.id}-{token}"


def validate_user_token(user_id: int, token: str) -> tuple[bool, User]:
    """ Validate user_id and token from url

    Args:
        user_id (int): id of the user to reset password
        token (str): django token to validate

    Returns:
        tuple[bool, User]:
            bool: True if user and token are valid, False otherwise
            User: user object
    """
    
    user = User.objects.filter(id=user_id, is_active=True)
    
    # render error message if user does not exist
    if not user.exists():
        return False, user
        
    user = user[0]
    
    # Validate token
    token_manager = PasswordResetTokenGenerator()
    is_valid = token_manager.check_token(user, token)
    
    # render error message if token is invalid
    if not is_valid:
        return False, user
    
    return True, user