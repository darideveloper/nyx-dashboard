from django.urls import path
from landing import views

urlpatterns = [
    # Api endpoints
    path('batch/', views.get_batch, name='batch'),
    path('texts/', views.get_texts, name='texts'),
    path('images/', views.get_images, name='images'),
    path('videos/', views.get_videos, name='videos'),
]
