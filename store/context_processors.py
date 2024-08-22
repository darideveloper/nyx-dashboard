from django.conf import settings


def load_env_variables(request):
    return {
        'LANDING_HOST': settings.LANDING_HOST,
        'IS_ADMIN': request.user.is_superuser,
    }