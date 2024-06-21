from django.urls import path
from landing import views

urlpatterns = [
    
    # redirect home to admin
    path('', views.home, name='home'),
    path('api/texts/', views.TextApi, name='texts'),
]
