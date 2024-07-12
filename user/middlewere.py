class AdminCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        
        # Get response
        
        response = self.get_response(request)
        domain = request.get_host()
        base_domain = "." + '.'.join(domain.split('.')[1:])
        is_local = False
        if "localhost" in domain or "127" in domain:
            is_local = True
        
        # Add or remove cookie
        if '/admin' in request.path and request.user.is_authenticated:
            name = f"{request.user.first_name} {request.user.last_name}"
            if is_local:
                response.set_cookie('nyx', name, path='/')
            else:
                response.set_cookie('nyx', name, path='/', domain=base_domain)
            
        elif "/logout" in request.path:
            if is_local:
                response.delete_cookie('nyx', path='/')
            else:
                response.delete_cookie('nyx', path='/', domain=base_domain)
            
        return response