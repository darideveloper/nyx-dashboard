from django.conf import settings
from store import models


def load_env_variables(request):
    
    # Validate if the user is an admin
    user_grups = request.user.groups.all()
    user_in_admin_group = False
    for group in user_grups:
        if group.name == "admins":
            user_in_admin_group = True
            break
        
    # Get current number of sets available
    sets_available = False
    current_stock = models.StoreStatus.objects.filter(key='current_stock')
    if current_stock.exists():
        current_stock = current_stock.first()
        if int(current_stock.value) > 0:
            sets_available = True
        
    return {
        'LANDING_HOST': settings.LANDING_HOST,
        'IS_ADMIN': request.user.is_superuser or user_in_admin_group,
        'SETS_AVAILABLE': sets_available,
    }