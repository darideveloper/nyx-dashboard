from bs4 import BeautifulSoup
from django.contrib.auth.models import User

from core.test_base.test_models import TestAffiliatesModelsBase
from core.test_base.test_admin import TestAdminBase

from store import models as store_models


class ComissionAdminTestCase(TestAdminBase, TestAffiliatesModelsBase):
    """Test admin views for Comission model as admin user"""

    def setUp(self):

        self.endpoint = "/admin/affiliates/comission/"
        super().setUp()

        # Create affiliate users
        self.password = "testpassword"
        self.affiliate_user1 = User.objects.create_user(
            "test1_aff", "test1@gmail.com", self.password, is_staff=True
        )
        self.affiliate_user2 = User.objects.create_user(
            "test2_aff", "test2@gmail.com", self.password, is_staff=True
        )

        self.affiliate1 = self.create_affiliate(self.affiliate_user1)
        self.affiliate2 = self.create_affiliate(self.affiliate_user2)

        # Comission for each affiliate
        self.commission_1_aff1 = self.create_comission(affiliate=self.affiliate1)
        self.commission_2_aff1 = self.create_comission(affiliate=self.affiliate1)
        self.commission_1_aff2 = self.create_comission(affiliate=self.affiliate2)
        self.commission_2_aff2 = self.create_comission(affiliate=self.affiliate2)

        # Global selectors
        self.selectors = {
            "rows": "tbody tr",
            "row_link": "th a",
        }

    def test_list_view_admin_all_comissions(self):
        """Test all sales visible for the admin user"""

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

        # Check if all sales are visible
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.select(self.selectors["rows"])
        self.assertEqual(len(rows), 4)

    def test_list_view_affiliate_self_comissions(self):
        """Test if affiliate user can only see their own sales"""

        # Login as affiliate user
        self.client.logout()
        self.client.login(
            username=self.affiliate_user1.username, password=self.password
        )

        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

        # Check if only the affiliate's sales are visible
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.select(self.selectors["rows"])
        self.assertEqual(len(rows), 2)

        # Validates sales ids
        ids = [self.commission_1_aff1.id, self.commission_2_aff1.id]
        hrefs = [row.select(self.selectors["row_link"])[0].get("href") for row in rows]
        hrefs_ids = [href.split("/")[-3] for href in hrefs]
        for id in ids:
            self.assertIn(id, hrefs_ids)

    def test_list_view_affiliate_no_paid_comissions(self):
        """Test if affiliate user can only see their own sales after pay state"""

        # Login as affiliate user
        self.client.logout()
        self.client.login(
            username=self.affiliate_user1.username, password=self.password
        )

        invalid_states = [
            "Pending",
            "Reminder Sent",
            "Payment Error",
        ]

        for state in invalid_states:
            self.commission_1_aff1.status = store_models.SaleStatus.objects.get(
                value=state
            )
            self.commission_1_aff1.save()

            response = self.client.get(self.endpoint)
            self.assertEqual(response.status_code, 200)

            # Check if only the affiliate's valid sales are visible
            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.select(self.selectors["rows"])
            self.assertEqual(len(rows), 1)

            # Check if the commission is not in the table
            for row in rows:
                href = row.select(self.selectors["row_link"])[0].get("href")
                self.assertNotIn(self.commission_2_aff2.id, href)


class ComissionAdminUserAffiliateTestCase(TestAffiliatesModelsBase):
    """Test admin views for Comission model as affiliate user"""

    pass
