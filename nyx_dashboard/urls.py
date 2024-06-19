from django.contrib import admin
from django.urls import path, include
from landing import urls as landing_urls

urlpatterns = [
    
    # redirect home to admin
    path('', include(landing_urls)),
    
    path('admin/', admin.site.urls),
]
