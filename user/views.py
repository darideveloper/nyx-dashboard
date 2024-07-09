from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
 

class SignUp(View):
    
    def get(self, request):
        return render(request, 'user/sign-up.html', context={
            "title": "Sign Up",
        })
    
    def post(self, request):
        
        # Get form fields
        email = request.POST.get("email")
        first_name = request.POST.get("first-name")
        last_name = request.POST.get("last-name")
        password1 = request.POST.get("password1")
        
        message_title = "Done"
        message_text = "User created successfully. " \
            "Check your email to confirm your account."
        message_type = "success"
        
        # Validate if the email is already used
        if User.objects.filter(username=email).exists():
            # Show error message
            message_title = "Error"
            message_text = "Email already used. " \
                "Try to login instead. " \
                "If you just created an account, check your email to activate it."
            message_type = "error"
        else:
            # Create user
            user = User.objects.create_user(
                email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password1,
                is_staff=True,
            )
            
            # Add user to group "buyers"
            buyers_group = Group.objects.get(name='buyers')
            buyers_group.user_set.add(user)
            
        return render(request, 'user/sign-up.html', context={
            "title": "Sign Up",
            "message_title": message_title,
            "message_text": message_text,
            "message_type": message_type,
        })
    
    
def redirect_login(request):
    return redirect('/admin/login/')


def redirect_sign_up(request):
    return redirect('/user/sign-up/')


def redirect_admin(request):
    return redirect('/admin/')


def activate(request, user_id):
    
    # Get user
    user = User.objects.get(id=user_id)
    
    # Rende html content
    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "texts": [
            "Thank you for signing up!",
            "Your account has been created successfully.",
            "Just one more step to start using it.",
        ],
        "cta_link": "/admin/login/",
        "cta_text": "Activate Now"
    }
    
    html_message = render_to_string('user/activation.html', context)
    plain_message = strip_tags(html_message)
    
    message = EmailMultiAlternatives(
        "Activate your account",
        plain_message,
        settings.EMAIL_HOST_USER,
        ["darideveloper@gmail.com"]
    )
    message.attach_alternative(html_message, "text/html")
    message.send()
    
    return render(request, 'user/activation.html', context=context)