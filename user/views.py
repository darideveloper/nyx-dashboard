from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.http import JsonResponse

class SignUp(View):
    
    def get(self, request):
        return render(request, 'sign-up.html', context={
            "title": "Sign Up",
            "password_reset_url": "/user/reset/"
        })
    
    def post(self, request):
        
        # Get form fields
        email = request.POST.get("email")
        first_name = request.POST.get("first-name")
        last_name = request.POST.get("last-name")
        password1 = request.POST.get("password1")
        
        return JsonResponse({
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password1": password1
        })
    
    
def redirect_login(request):
    return redirect('/admin/login/')


def redirect_sign_up(request):
    return redirect('/user/sign-up/')