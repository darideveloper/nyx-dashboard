from django.conf import settings


def get_media_url(object_or_url: object) -> str:
    """ Return the media url for the image (local or s3).
    
    Args:
        url (object): image object or url string
        
    Returns:
        str: url of the image
    """
        
    # Get the url string
    url_str = ""
    if type(object_or_url) is str:
        url_str = object_or_url
    else:
        url_str = object_or_url.url
    
    if "s3.amazonaws.com" not in url_str:
        return f"{settings.HOST}{url_str}"
    return url_str