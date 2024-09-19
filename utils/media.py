from django.conf import settings


def get_media_url(url: str) -> str:
    """ Return the media url for the image (local or s3).
    
    Args:
        url (str): url of the image
        
    Returns:
        str: url of the image
    """
    if "s3.amazonaws.com" not in url:
        return f"{settings.HOST}{url}"
    return url