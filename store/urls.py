from django.urls import path
from store import views

urlpatterns = [
    # Api endpoints
    path('next-future-stock/', views.get_next_future_stock, name='next-future-stock'),
]
