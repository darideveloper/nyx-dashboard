from django.urls import path
from store import views

urlpatterns = [
    # Api endpoints
    path('next-future-stock/<email>',
         views.NextFutureStock.as_view(), name='next-future-stock'),
    path('next-future-stock/',
         views.NextFutureStock.as_view(), name='next-future-stock'),
    path('future-stock-subscription/',
         views.FutureStockSubscription.as_view(), name='future-stock-subscription'),
    path('sale/', views.Sale.as_view(), name='sale'),
    path('current-stock/', views.CurrentStock.as_view(), name='current-stock'),
    path('sale-done/<sale_id>/', views.SaleDone.as_view(), name='sale-done'),
]
