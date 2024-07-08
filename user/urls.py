from django.urls import path
from user import views

urlpatterns = [
    
    # Api endpoints
    path('sign-up/', views.SignUp.as_view(), name='sign-up'),
]
