import os
from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from dotenv import load_dotenv
from user import decorators
from django.utils.decorators import method_decorator
from utils import emails, tokens


# Load environment variables
load_dotenv()
HOST = os.getenv("HOST")


class SignUpView(View):

    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
    def get(self, request):
        
        # Render form
        return render(request, 'user/sign-up.html', context={
            "title": "Sign Up",
        })

    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
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
            id_token = tokens.get_id_token(user)
       
            emails.send_email(
                subject="Activate your Nyx Trackers account",
                first_name=first_name,
                last_name=last_name,
                texts=[
                    "Thank you for signing up!",
                    "Your account has been created successfully.",
                    "Just one more step to start using it.",
                ],
                cta_link=f"{HOST}/user/activate/{id_token}/",
                cta_text="Activate Now",
                to_email=email,
            )

        return render(request, 'user/sign-up.html', context={
            "title": "Sign Up",
            "message_title": message_title,
            "message_text": message_text,
            "message_type": message_type,
        })


class ActivateView(View):
    
    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
    def get(self, request, user_id: int, token: str):
        
        title = "Activation"
        
        user = User.objects.filter(id=user_id)
        
        error_context = {
            "title": title,
            "message_title": "Activation Error",
            "message_text": "Check the link or try to sign up again.",
            "message_type": "error",
            "redirect": "/user/sign-up/",
        }
        error_response = render(request, 'admin/login.html', context=error_context)
        
        is_valid, user = tokens.validate_user_token(user_id, token, filter_active=False)
        
        # render error message if token is invalid
        if not is_valid:
            return error_response
        
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


class ForgottenPassView(View):
    
    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
    def get(self, request):
        """ Render forgotten pass tamplate """
        
        # Render form
        return render(request, 'user/forgotten-pass.html', context={
            "title": "Forgotten Password",
        })
    
    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
    def post(self, request):
        """ Sent reset email or reset pass """
        
        context = {
            "title": "Forgotten Password",
            "message_title": "Email sent",
            "message_text": "If your email is registered, "
                            "you will receive an email with instructions "
                            "to reset your password.",
            "message_type": "success",
            "redirect": "/admin/login/",
        }
        rendered_template = render(request, 'user/forgotten-pass.html', context)
    
        # Get email from form
        email = request.POST.get("email")
        
        # Validate if the email exists
        user = User.objects.filter(username=email)
        if not user.exists():
            return rendered_template
        user = user[0]
        
        # Generate token
        id_token = tokens.get_id_token(user)
        
        emails.send_email(
            subject="Reset your Nyx Trackers password",
            first_name=user.first_name,
            last_name=user.last_name,
            texts=[
                "Did you forget your password? No worries!",
                "Click the button below to reset it.",
                "If you didn't request this, you can ignore this email.",
            ],
            cta_link=f"{HOST}/user/reset-pass/{id_token}/",
            cta_text="Reset Password",
            to_email=email,
        )
            
        # Return the email preview
        return rendered_template
    
    
class ResetPassView(View):
    
    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
    def get(self, request, user_id: int, token: str):
        
        title = "Reset Password"
        
        # Generate error response
        error_context = {
            "title": title,
            "message_title": "Reset Password Error",
            "message_text": "Check the link or try to reset your password again.",
            "message_type": "error",
            "redirect": "/user/forgotten-pass/",
        }
        error_response = render(request, 'user/reset-pass.html', context=error_context)
        
        is_valid, user = tokens.validate_user_token(user_id, token)
        if not is_valid:
            return error_response
        
        # Render form
        return render(request, 'user/reset-pass.html', context={
            "title": title,
            "email": user.username,
        })
    
    @method_decorator(decorators.not_logged(redirect_url='/admin/'))
    def post(self, request, user_id: int, token: str):
        
        title = "Reset Password"
        
        user = User.objects.filter(id=user_id)
        
        # Generate error response
        error_context = {
            "title": title,
            "message_title": "Reset Password Error",
            "message_text": "Check the link or try to reset your password again.",
            "message_type": "error",
            "redirect": "/user/forgotten-pass/",
        }
        error_response = render(request, 'user/reset-pass.html', context=error_context)
        
        is_valid, user = tokens.validate_user_token(user_id, token)
        if not is_valid:
            return error_response
        
        # Update password from form
        new_password = request.POST.get("new-password-1")
        user.set_password(new_password)
        user.save()
        
        # Success message
        return render(request, 'user/reset-pass.html', context={
            "title": title,
            "message_title": "Password Updated",
            "message_text": "Your password has been updated successfully. "
                            "Now you can login.",
            "message_type": "success",
            "redirect": "/admin/login/",
            "email": user.username,
        })