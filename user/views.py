from django.shortcuts import render
from django.views import View


class SignUp(View):
    
    def get(self, request):
        return render(request, 'sign-up.html', context={"title": "Sign Up"})
    
    def post(self, request):
        return render(request, 'sign-up.html', context={"title": "Sign Up"})