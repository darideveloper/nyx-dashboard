from django.contrib import admin
from django.urls import path, include
from landing import urls as landing_urls
from user import urls as user_urls
from landing import views as views_landing
from user import views as views_user

urlpatterns = [
    
    # redirect home to admin
    path('', views_landing.home, name='home'),
    path('api/', include(landing_urls)),
    path('user/', include(user_urls)),
    path('admin/', admin.site.urls),
    path('login/', views_user.redirect_login, name='redirect-login'),
    path('sign-up/', views_user.redirect_sign_up, name='redirect-sign-up'),
    path('accounts/profile/', views_user.redirect_admin, name='redirect-admin'),
]
