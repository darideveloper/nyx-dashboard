import os
from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from user import tools
from dotenv import load_dotenv
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.http import JsonResponse


# Load environment variables
load_dotenv()
HOST = os.getenv("HOST")


class SignUp(View):

    def get(self, request):
        
        # Redirect to admin if user is already logged in
        if request.user.is_authenticated:
            return redirect('/admin/')
        
        # Render form
        return render(request, 'user/sign-up.html', context={
            "title": "Sign Up",
        })

    def post(self, request):
        
        send_email = True

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
        user = User.objects.filter(username=email)
        if user.exists():
            
            user = user[0]
            
            # Error if user its already active
            if user.is_active:
                message_title = "Error"
                message_text = "Email already used. " \
                    "Try to login instead. " \
                    "If you just created an account, " \
                    "check your email to activate it."
                message_type = "error"
                send_email = False
            else:
                # Send activation email
                message_text = "Account already created. " \
                    "Check your email to confirm your account."
        else:
            # Create user
            user = User.objects.create_user(
                email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password1,
                is_staff=True,
                is_active=False,
            )

            # Add user to group "buyers"
            buyers_group = Group.objects.get(name='buyers')
            buyers_group.user_set.add(user)


        # Send activation email
        if send_email:
       
            # Generate token
            token_manager = PasswordResetTokenGenerator()
            user_token = token_manager.make_token(user)
       
            tools.send_email(
                subject="Activate your Nyx Trackers account",
                first_name=first_name,
                last_name=last_name,
                texts=[
                    "Thank you for signing up!",
                    "Your account has been created successfully.",
                    "Just one more step to start using it.",
                ],
                cta_link=f"{HOST}/user/activate/{user.id}-{user_token}/",
                cta_text="Activate Now",
                to_email=email,
            )

        return render(request, 'user/sign-up.html', context={
            "title": "Sign Up",
            "message_title": message_title,
            "message_text": message_text,
            "message_type": message_type,
        })


class Activate(View):
    
    def get(self, request, user_id, token):
        
        title = "Activation"
        
        user = User.objects.filter(id=user_id)
        
        error_context = {
            "title": title,
            "message_title": "Activation Error",
            "message_text": "Check the link or try to sign up again.",
            "message_type": "error",
            "redirect": "/user/sign-up/",
        }
        
        # render error message if user does not exist
        if not user.exists():
            return render(request, 'admin/login.html', context=error_context)
            
        user = user[0]
        
        # Validate token
        token_manager = PasswordResetTokenGenerator()
        is_valid = token_manager.check_token(user, token)
        
        # render error message if token is invalid
        if not is_valid:
            return render(request, 'admin/login.html', context=error_context)
        
        # Activate user
        user.is_active = True
        user.save()
        
        # Success message
        return render(request, 'admin/login.html', context={
            "title": title,
            "message_title": "Account Activated",
            "message_text": "Your account has been activated successfully. "
                            "Now you can login.",
            "message_type": "success",
            "redirect": "/admin/login/",
            "skip_no_auth_message": True,
        })
    

def redirect_login(request):
    return redirect('/admin/login/')


def redirect_sign_up(request):
    return redirect('/user/sign-up/')


def redirect_admin(request):
    return redirect('/admin/')


def preview_email_activation(request):

    # Render the email template
    context = {
        "first_name": "dari",
        "last_name": "dev",
        "texts": [
            "Thank you for signing up!",
            "Your account has been created successfully.",
            "Just one more step to start using it.",
        ],
        "cta_link": f"{HOST}/user/activate/12345/",
        "cta_text": "Activate Now",
    }
        
    # Return the email preview
    return render(request, 'user/email.html', context)
