import random
import string

from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission

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
            random_username = "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
            user = User.objects.create_user(
                username=random_username,
                email="test@gmail.com",
                password="testpassword",
            )

        # Create promo code if not provided
        if not promo_code:
            promo_code_type = store_models.PromoCodeType.objects.get(name="percentage")
            promo_code = store_models.PromoCode.objects.create(
                code=f"TESTCODE-{user.username}",
                discount=10.00,
                type=promo_code_type,
            )

        # Create affiliate instance
        affiliate = models.Affiliate.objects.create(
            user=user,
            social_media=social_media,
            promo_code=promo_code,
            balance=balance,
        )

        # Create affiliates group and add permissions
        group, group_created = Group.objects.get_or_create(name="affiliates")
        if group_created:
            permissions_names = [
                "Can view comission",
            ]
            permissions = Permission.objects.filter(name__in=permissions_names)
            for permission in permissions:
                group.permissions.add(permission)
        group.user_set.add(user)
        group.save()

        return affiliate

    def create_comission(
        self,
        affiliate: models.Affiliate = None,
        user: User = None,
        status: str = "Paid",
    ) -> models.Comission:
        """
        Helper method to create a Comission instance.

        Args:
            affiliate (Affiliate): The Affiliate instance associated with the Comission.
            user (User): The User instance associated with the Comission (buyer).
            status (str): The status of the sale. Defaults to "completed".

        Returns:
            Comission: The created Comission instance (proxy for Sale).
        """

        # Create random client if not exists
        if not user:
            username_lenght = random.randint(5, 15)
            random_string = "".join(
                random.choices(string.ascii_letters + string.digits, k=username_lenght)
            )
            user = User.objects.create_user(
                username=random_string,
                email="user@email.com",
                password="testpassword",
            )

        # Create django user if not provided and get promo code
        if not affiliate:
            affiliate = self.create_affiliate()
        promo_code = affiliate.promo_code

        # Create sale / comission
        comission = models.Comission.objects.create(
            user=user,
            set=store_models.Set.objects.all().first(),
            colors_num=store_models.ColorsNum.objects.all().first(),
            color_set=store_models.Color.objects.all().first(),
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=random.randint(100, 10000),
            status=store_models.SaleStatus.objects.get(value=status),
            promo_code=promo_code,
        )

        return comission
