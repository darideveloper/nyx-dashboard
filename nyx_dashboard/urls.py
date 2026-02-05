from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from landing import urls as landing_urls
from store import urls as store_urls
from user import urls as user_urls
from landing import views as views_landing
from user import views as views_user
from affiliates import urls as affiliates_urls


urlpatterns = [
    # redirect home to admin
    path("", views_landing.home, name="home"),
    # Api urls
    path("api/landing/", include(landing_urls)),
    path("api/store/", include(store_urls)),
    path("api/affiliates/", include(affiliates_urls)),
    # Authentication urls
    path("user/", include(user_urls)),
    path("admin/", admin.site.urls),
    path("login/", views_user.redirect_login, name="redirect-login"),
    path("sign-up/", views_user.redirect_sign_up, name="redirect-sign-up"),
    path("accounts/profile/", views_user.redirect_admin, name="redirect-admin"),
    # Tools urls
    path("landing/", views_user.redirect_landing, name="redirect-landing"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
