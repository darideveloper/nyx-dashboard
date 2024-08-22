from django.urls import path
from store import views

urlpatterns = [
    # Api endpoints
    path('next-future-stock/<email>',
         views.get_next_future_stock, name='next-future-stock'),
    path('next-future-stock/',
         views.get_next_future_stock, name='next-future-stock'),
    path('future-stock-subscription/',
         views.FutureStockSubscription.as_view(), name='future-stock-subscription'),
    path('sale/', views.Sale.as_view(), name='Sale'),
    path('current-stock/', views.CurrentStock.as_view(), name='current-stock'),
]
