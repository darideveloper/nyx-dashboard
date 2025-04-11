from django.contrib import admin
from .models import Comission, Affiliate


class AffiliateFilter(admin.SimpleListFilter):
    title = "Affiliate"
    parameter_name = "affiliate"

    def lookups(self, request, model_admin):
        # Provide a list of affiliates for filtering
        affiliates = Affiliate.objects.all()
        return [(affiliate.id, affiliate.name) for affiliate in affiliates]

    def queryset(self, request, queryset):
        # Filter commissions by the selected affiliate
        if self.value():
            return queryset.filter(promo_code__affiliate__id=self.value())
        return queryset


@admin.register(Affiliate)
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


@admin.register(Comission)
class ComissionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "promo_code", "affiliate", "total", "status")
    list_filter = (AffiliateFilter, "created_at")
