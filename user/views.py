import os
from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from user import tools
from dotenv import load_dotenv
from django.contrib.auth.tokens import PasswordResetTokenGenerator


# Load environment variables
load_dotenv()
HOST = os.getenv("HOST")


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

            # Generate token
            token_manager = PasswordResetTokenGenerator()
            user_token = token_manager.make_token(user)

            # Send activation email
            tools.send_email(
                subject="Activate your Nyx Trackers account",
                first_name=first_name,
                last_name=last_name,
                texts=[
                    "Thank you for signing up!",
                    "Your account has been created successfully.",
                    "Just one more step to start using it.",
                ],
                cta_link=f"{HOST}/user/activate/{user_token}/",
                cta_text="Activate Now",
                to_email=email,
            )

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
