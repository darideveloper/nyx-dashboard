from user import views
from django.urls import path
from django.urls import include

urlpatterns_preview_email = [
    path('acivate/', views.preview_email_activation, name='activate')
]

urlpatterns = [
    # Custom user page
    path('sign-up/', views.SignUp.as_view(), name='sign-up'),
    path('email-preview/', include(urlpatterns_preview_email)),
]
