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
    search_fields = ("user__username", "user__email", "promo_code__code")
    list_filter = ("user__is_active",)


@admin.register(models.Comission)
class ComissionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "total")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    list_per_page = 20