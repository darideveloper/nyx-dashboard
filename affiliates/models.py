from django.db import models
from django.contrib.auth.models import User

from store import models as store_models


class Affiliate(models.Model):
    """Affiliate model for managing affiliate information"""

    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="affiliate",
        verbose_name="Usuario",
        null=True,
        blank=True,
    )
    social_media = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Social media link for the affiliate (e.g., Instagram, Facebook)",
    )
    promo_code = models.OneToOneField(
        store_models.PromoCode,
        on_delete=models.SET_NULL,
        verbose_name="Código promocional",
        null=True,
        blank=True,
    )
    balance = models.FloatField(default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Afiliado"
        verbose_name_plural = "Afiliados"

    def __str__(self):
        return f"{self.name}"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def active(self):
        return self.user.is_active


class Comission(store_models.Sale):
    """ Comission model for affiliates, from store sale"""

    class Meta:
        proxy = True
        verbose_name = "Comisión"
        verbose_name_plural = "Comisiones"

    @property
    def affiliate(self):
        promo_code = self.promo_code
        affioliate = Affiliate.objects.filter(promo_code=promo_code).first()
        return affioliate if promo_code else None
