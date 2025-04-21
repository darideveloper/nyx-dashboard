from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command

from core.test_base.test_models import TestAffiliatesModelsBase


class SaleViewTestCase(TestAffiliatesModelsBase):
    """ Sale view to validate behavior in affiliate models """

    def setUp(self):
        
        call_command("apps_loaddata")

        super().setUp()

        # Create affiliate users
        self.password = "testpassword"
        self.affiliate_user = User.objects.create_user(
            "test1_aff", "test1@gmail.com", self.password, is_staff=True
        )

        self.affiliate = self.create_affiliate(self.affiliate_user)

        # Comission for each affiliate
        self.comission = self.create_comission(
            affiliate=self.affiliate, status="Pending"
        )

    def test_comission_applied_affiliate(self):
        """Test if comission is applied to the affiliate when payment is made"""

        # Simulate a payment made to the affiliate
        res = self.client.get(
            f"/api/store/sale-done/{self.comission.id}/?use_testing=true"
        )
        self.assertEqual(res.status_code, 302)

        # Validate sale status
        self.comission.refresh_from_db()
        self.assertEqual(self.comission.status.value, "Paid")

        # Validate commission applied
        self.assertEqual(
            self.comission.affiliate.balance,
            self.comission.total * settings.AFFILIATES_COMMISSION,
        )
