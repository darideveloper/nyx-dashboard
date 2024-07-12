from functools import wraps
from django.shortcuts import redirect


def not_logged(redirect_url='/'):
    """ Redirect to admin if the user is logged in """
    
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            
            is_logged = request.user.is_authenticated
            if not is_logged:
                return function(request, *args, **kwargs)
            else:
                return redirect(redirect_url)
        return wrap
    return decorator