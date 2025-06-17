from time import sleep

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from core.test_base.test_models import TestAffiliatesModelsBase
from core.test_base.test_admin import TestAdminBase, TestAdminSeleniumBase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.apps import apps

from store import models as store_models


class ComissionAdminTestCase(TestAffiliatesModelsBase, TestAdminBase):
    """Test admin views for Comission model as admin user"""

    def setUp(self):

        # Load all apps permissions
        for app_config in apps.get_app_configs():
            create_permissions(app_config, verbosity=0)

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


class ComissionAdminTestCaseLive(TestAffiliatesModelsBase, TestAdminSeleniumBase):
    """Test admin views for Comission model as admin user"""

    def setUp(self):

        super().setUp("/admin/affiliates/comission/", auto_login=False)

        # Create affiliate users
        self.password = "testpassword"
        self.affiliate_user1 = User.objects.create_user(
            "test1_aff", "test1@gmail.com", self.password, is_staff=True
        )

        self.affiliate1 = self.create_affiliate(self.affiliate_user1)

        # Comission for each affiliate
        self.commission_1_aff1 = self.create_comission(affiliate=self.affiliate1)
        self.commission_2_aff1 = self.create_comission(affiliate=self.affiliate1)
        # Global selectors
        self.selectors = {
            "rows": "tbody tr",
            "row_link": "th a",
            "filters": {
                "promo": '[data-name="promo_code__affiliate"]',
                "date": '[data-name="created_at"]',
                "status": '[data-name="status"]',
                "wrapper": "#changelist-search",
            },
        }

    def __affiliate_login__(self):
        """Login as affiliate user"""
        self.admin_user = self.affiliate_user1.username
        self.admin_pass = self.password
        self.__login__()

    def test_list_view_links_disable_affiliate(self):
        """Test if the links are disabled for the affiliate user"""

        self.__affiliate_login__()

        # Get the rows links
        links_full_selector = self.selectors["rows"] + " " + self.selectors["row_link"]
        links = self.driver.find_elements(By.CSS_SELECTOR, links_full_selector)

        # Check if the links are disabled
        for link in links:
            self.assertEqual(link.get_attribute("href"), None)

    def test_list_view_links_enable_admin(self):
        """Test if the links are enabled for the admin user"""

        self.__login__()

        # Get the rows links
        links_full_selector = self.selectors["rows"] + " " + self.selectors["row_link"]
        links = self.driver.find_elements(By.CSS_SELECTOR, links_full_selector)

        # Check if the links are enabled
        for link in links:
            self.assertNotEqual(link.get_attribute("href"), None)

    def test_list_view_hide_filters_affiliate(self):
        """Test if the filters are not visible for the affiliate user"""

        self.__affiliate_login__()

        # Get the filters
        elems = self.get_selenium_elems(self.selectors["filters"])

        # Check if the filters are not visible
        for elem in elems.values():
            self.assertIsNone(elem)

    def test_list_view_show_filters_admin(self):
        """Test if the filters are not visible for the admin user"""

        self.__login__()

        # Get the filters
        elems = self.get_selenium_elems(self.selectors["filters"])

        # Check if the filters are not visible
        for elem in elems.values():
            self.assertIsNotNone(elem)


class AffiliateAdminTestCase(TestAdminBase):

    def setUp(self):

        # Submit endpoint
        super().setUp()
        self.endpoint = "/admin/affiliates/affiliate/"

    def test_search_bar(self):
        """Validate search bar working"""

        self.submit_search_bar(self.endpoint)


class AffiliateAdminListViewwTestCaseLive(
    TestAffiliatesModelsBase, TestAdminSeleniumBase
):
    """Test admin views for Affiliate model as admin user"""

    def setUp(self):

        # Load data
        call_command("apps_loaddata")

        # Create affiliate users
        self.affiliate1 = self.create_affiliate()
        self.affiliate2 = self.create_affiliate()
        self.affiliate2.promo_code = None
        self.affiliate2.save()

        super().setUp("/admin/affiliates/affiliate/")

        self.selectors = {
            "btn_edit": ".btn-edit",
            "btn_create": ".btn-create",
            "promocode_label": ".promocode-wrapper span",
            "alert": ".alert-success",
        }

    def test_custom_btns_promo_code_edit(self):
        """
        Validate behavior of the edit custom button
        Should redirect to the promo code page
        """

        # Click the edit button
        btn = self.get_selenium_elem(self.selectors["btn_edit"])
        btn.click()

        # Check if the page is redirected to the promo code page
        self.assertIn("/admin/store/promocode/", self.driver.current_url)
        self.assertIn("/change", self.driver.current_url)

    def test_custom_btns_promo_code_create(self):
        """
        Validate behavior of the create custom button
        Should create a new promo code based on the affiliate
        """

        # Click the create button
        btn = self.get_selenium_elem(self.selectors["btn_create"])
        btn.click()

        # Validate be in the same page
        self.assertIn(self.endpoint, self.driver.current_url)

        # Validate message
        alert = self.get_selenium_elem(self.selectors["alert"])
        self.assertIsNotNone(alert)
        self.assertIn("Promo code ", alert.text)
        self.assertIn(" created successfully", alert.text)

    def test_custom_btns_promo_code_create_already_exists(self):
        """
        Validate behavior of the create custom button, when the promo code already exists
        Should use the existing promo code and change the data
        """

        # Delete affiliate without promo code
        self.affiliate1.delete()
        store_models.PromoCode.objects.all().delete()
        sleep(1)

        self.driver.refresh()

        # Manually create a promo code with username
        promo_code_type = store_models.PromoCodeType.objects.get(name="amount")
        promo_code = store_models.PromoCode(
            code=self.affiliate2.user.username,
            type=promo_code_type,
            discount=100,
        )
        promo_code.save()

        # Click the create button
        btn = self.get_selenium_elem(self.selectors["btn_create"])
        btn.click()

        # Validate be in the same page
        self.assertIn(self.endpoint, self.driver.current_url)

        # Validate message
        alert = self.get_selenium_elem(self.selectors["alert"])
        self.assertIsNotNone(alert)
        self.assertIn("Promo code ", alert.text)
        self.assertIn(" created successfully", alert.text)

        # Validate promo code updated and assigned to the affiliate
        promo_code.refresh_from_db()
        self.affiliate2.refresh_from_db()
        self.assertEqual(promo_code.discount, settings.AFFILIATES_DISCOUNT * 100)
        self.assertEqual(promo_code.type.name, "percentage")
        self.assertEqual(self.affiliate2.promo_code, promo_code)

    def test_custom_btns_promo_code_rendered_promocode(self):
        """
        Validate current promo code visible
        """
        
        # Delete first affiliate
        self.affiliate1.delete()
        sleep(1)
        
        # refresh page
        self.driver.refresh()
        
        # Click in the create button
        btn = self.get_selenium_elem(self.selectors["btn_create"])
        btn.click()
        
        # Validate text of the promo code created
        text = self.get_selenium_elem(self.selectors["promocode_label"]).text
        self.assertEqual(self.affiliate2.user.username, text)


class PaymentAdminTestCase(TestAdminBase):

    def setUp(self):

        # Submit endpoint
        super().setUp()
        self.endpoint = "/admin/affiliates/payment/"

    def test_search_bar(self):
        """Validate search bar working"""

        self.submit_search_bar(self.endpoint)