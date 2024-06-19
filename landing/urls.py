from django.contrib import admin
from django.urls import path
from landing import views

urlpatterns = [
    
    # redirect home to admin
    path('', views.home),
]
