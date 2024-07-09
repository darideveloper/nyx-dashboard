from django.urls import path
from user import views

urlpatterns = [
    
    # Custom user page
    path('sign-up/', views.SignUp.as_view(), name='sign-up'),
    path('activate/<int:user_id>', views.activate, name='activate'),
]
