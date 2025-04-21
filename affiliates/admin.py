from django.contrib import admin
from django.utils.html import format_html


from affiliates import models
from utils.admin import is_user_admin


@admin.register(models.Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "active",
        "btns_promo_code",
        "balance",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__username", "user__email", "promo_code__code")
    list_filter = ("user__is_active",)

    # Custom fields
    def btns_promo_code(self, obj):
        current_promo_code = obj.promo_code
        if current_promo_code:
            link = f"/admin/store/promocode/{current_promo_code.id}/change/"
            btn_class = "btn-warning btn-edit"
            btn_text = "Edit"
            code = current_promo_code.code
        else:
            link = f"/api/affiliates/promocode/create/{obj.id}/"
            btn_class = "btn-success btn-create"
            btn_text = "Create"
            code = ""
            
        html = """
        <p class="promocode-wrapper">
            <a href="{}" class="btn {}">
                {}
            </a>
            <span>{}</span>
        </p>
        """

        return format_html(
            html,
            link,
            btn_class,
            btn_text,
            code,
        )

    # Label the custom field
    btns_promo_code.short_description = "Códigos promocionales"


@admin.register(models.Comission)
class ComissionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "promo_code", "affiliate", "total", "status")
    list_filter = ("promo_code__affiliate", "created_at", "status")
    list_display_links = ("created_at",)

    def get_queryset(self, request):

        # Get admin type
        user_auth = request.user

        # Validte if user is in "admins" group
        user_admin = is_user_admin(request.user)

        if not user_admin:

            # Get only done or after affiliate promo code commission
            visible_states = [
                "Paid",
                "Manufacturing",
                "Shipped",
                "Delivered",
            ]
            promo_codes = models.Affiliate.objects.filter(user=user_auth)
            if not promo_codes:
                return models.Comission.objects.none()
            promo_code = promo_codes[0].promo_code
            comission_affiliate = models.Comission.objects.filter(promo_code=promo_code)
            comission_affiliate_valid = comission_affiliate.filter(
                status__value__in=visible_states
            )
            return comission_affiliate_valid

        # Render all promo code comissions
        affiliates = models.Affiliate.objects.all()
        promo_codes = [affiliate.promo_code for affiliate in affiliates]
        return models.Comission.objects.filter(promo_code__in=promo_codes)

    class Media:
        js = (
            "affiliates/js/disbale_details_link.js",
            "affiliates/js/disbale_filters.js",
        )


@admin.register(models.Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("affiliate", "amount", "payment_date", "status")
    list_filter = ("affiliate", "status")
    search_fields = ("affiliate__user__username", "affiliate__user__email")
