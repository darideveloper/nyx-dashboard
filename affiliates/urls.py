from django.urls import path
from affiliates import views

urlpatterns = [
    # Api endpoints
    path(
        "promocode/create/<int:affiliate_id>/",
        views.AffiliatePromoCodeCreateView.as_view(),
        name="promocode-create",
    ),
]
