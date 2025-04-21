from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View

from affiliates import models
from store import models as store_models


class AffiliatePromoCodeCreateView(View):
    """View to create a promo code for an affiliate"""

    def get(self, request, affiliate_id):
        """Create a promo code for the affiliate"""

        # Gat affiliate
        affiliate = models.Affiliate.objects.get(id=affiliate_id)

        # Crate promo code with affiliate username
        promo_code_type = store_models.PromoCodeType.objects.get(name="percentage")
        promo_codes = store_models.PromoCode.objects.filter(
            code=affiliate.user.username,
        )
        if promo_codes.exists():
            # Update existing promo code
            promo_code = promo_codes.first()
            promo_code.type = promo_code_type
            promo_code.discount = settings.AFFILIATES_DISCOUNT
            promo_code.save()
        else:
            # Create new promo code
            promo_code = store_models.PromoCode(
                code=affiliate.user.username,
                type=promo_code_type,
                discount=settings.AFFILIATES_DISCOUNT,
            )
            promo_code.save()

        # Add promo code to affiliate
        affiliate.promo_code = promo_code
        affiliate.save()

        # Redirect to the affiliate page with a message
        messages.success(
            request,
            f"Promo code {promo_code.code} created successfully for {affiliate}",
        )
        return redirect("/admin/affiliates/affiliate/")
