from django.contrib import admin
from affiliates import models


@admin.register(models.Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "active",
        "promo_code",
        "balance",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "email", "promo_code")
    list_filter = ("active",)
    ordering = ("-created_at",)
    list_per_page = 20
