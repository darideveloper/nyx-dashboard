from django.test import TestCase
from django.contrib.auth.models import User

from store import models as store_models
from affiliates import models


class TestAffiliatesModelsBase(TestCase):
    """Base test class for validating model custom methods and helpers."""

    def create_affiliate(
        self,
        user: User = None,
        social_media: str = "https://instagram.com/testuser",
        promo_code: store_models.PromoCode = None,
        balance: float = 0.00,
    ) -> models.Affiliate:
        """
        Helper method to create an Affiliate instance.

        Args:
            user (User): The User instance associated with the Affiliate.
            social_media (str): The social media link. Defaults to a test URL.
            promo_code (PromoCode): The PromoCode instance associated with the Affiliate.
            balance (float): The balance of the affiliate. Defaults to 0.00.

        Returns:
            Affiliate: The created Affiliate instance.
        """

        # Create django user if not provided
        if not user:
            user = User.objects.create_user(
                username="testuser", email="test@gmail.com", password="testpassword"
            )

        # Create promo code if not provided
        if not promo_code:
            promo_code_type = store_models.PromoCodeType.objects.get(name="percentage")
            promo_code = store_models.PromoCode.objects.create(
                code=f"TESTCODE-{user.username}",
                discount=10.00,
                type=promo_code_type,
            )

        return models.Affiliate.objects.create(
            user=user,
            social_media=social_media,
            promo_code=promo_code,
            balance=balance,
        )

    def create_comission(
        self,
        affiliate: models.Affiliate = None,
        total: float = 50.00,
        status: str = "completed",
    ) -> models.Comission:
        """
        Helper method to create a Comission instance.

        Args:
            affiliate (Affiliate): The Affiliate instance associated with the Comission.
            total (float): The total amount of the sale. Defaults to 50.00.
            status (str): The status of the sale. Defaults to "completed".

        Returns:
            Comission: The created Comission instance (proxy for Sale).
        """
        pass
