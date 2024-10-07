from django.conf import settings


def load_env_variables(request):
    
    user_grups = request.user.groups.all()
    user_in_admin_group = False
    for group in user_grups:
        if group.name == "admins":
            user_in_admin_group = True
            break
    
    return {
        'LANDING_HOST': settings.LANDING_HOST,
        'IS_ADMIN': request.user.is_superuser or user_in_admin_group,
    }