from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """
    Handles static files (CSS, JS, images).
    Stored in: bucket/project_folder/static/
    """

    location = settings.STATIC_LOCATION
    default_acl = "public-read"


class PublicMediaStorage(S3Boto3Storage):
    """
    Handles public uploads (user avatars, post images).
    Stored in: bucket/project_folder/media/
    """

    location = settings.PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """
    Handles sensitive files (documents, private videos).
    Stored in: bucket/project_folder/private/
    """

    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False
    # Crucial: Private files must bypass the CDN to use Signed URLs
    custom_domain = False
