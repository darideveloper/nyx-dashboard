class AdminCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        
        # Get response
        
        response = self.get_response(request)
        
        # Add or remove cookie
        if '/admin' in request.path and request.user.is_authenticated:
            name = f"{request.user.first_name} {request.user.last_name}"
            response.set_cookie('nyx', name, path='/')
            print(f'Cookie set: {request.user.first_name}')
            
        elif "/logout" in request.path:
            response.delete_cookie('nyx')
            print('Cookie deleted')
            
        return response