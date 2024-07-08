from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect


class SignUp(View):
    
    def get(self, request):
        return render(request, 'sign-up.html', context={
            "title": "Sign Up",
            "password_reset_url": "/user/reset/"
        })
    
    def post(self, request):
        return render(request, 'sign-up.html', context={"title": "Sign up"})
    
    
def redirect_login(request):
    return redirect('/admin/login/')


def redirect_sign_up(request):
    return redirect('/user/sign-up/')