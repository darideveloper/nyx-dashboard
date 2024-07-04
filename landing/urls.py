from django.urls import path
from landing import views

urlpatterns = [
    
    # redirect home to admin
    path('', views.home, name='home'),
    
    # Api endpoints
    path('api/texts/', views.get_texts, name='texts'),
    path('api/images/', views.get_images, name='images'),
    path('api/videos/', views.get_videos, name='videos'),
]
