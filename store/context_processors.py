from django.conf import settings
from store import models
from utils.admin import is_user_admin


def load_env_variables(request):
    
    # Validate if the user is an admin
    user_admin = is_user_admin(request.user)
        
    # Get current number of sets available
    sets_available = False
    current_stock = models.StoreStatus.objects.filter(key='current_stock')
    if current_stock.exists():
        current_stock = current_stock.first()
        if int(current_stock.value) > 0:
            sets_available = True
        
    return {
        'LANDING_HOST': settings.LANDING_HOST,
        'IS_ADMIN': user_admin,
        'SETS_AVAILABLE': sets_available,
    }