from user import views
from django.urls import path
from django.urls import include

urlpatterns_preview_email = [
    path('acivate/', views.preview_email_activation, name='activate')
]

urlpatterns = [
    path('email-preview/', include(urlpatterns_preview_email)),
    path('sign-up/', views.SignUp.as_view(), name='sign-up'),
    path('activate/<int:user_id>-<token>/', views.Activate.as_view(), name='activate'),
]
