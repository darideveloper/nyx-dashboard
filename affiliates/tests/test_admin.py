from bs4 import BeautifulSoup
from django.contrib.auth.models import User

from core.test_base.test_models import TestAffiliatesModelsBase
from core.test_base.test_admin import TestAdminBase


class ComissionAdminUserAdminTestCase(TestAffiliatesModelsBase, TestAdminBase):
    """Test admin views for Comission model as admin user"""

    def setUp(self):
        
        self.endpoint = "/admin/affiliates/comission/"
        super().setUp()
        
        # Create users
        user1 = User.objects.create_user("test1", "test1@gmail.com", "testpassword")
        user2 = User.objects.create_user("test2", "test2@gmail.com", "testpassword")

        # Create models
        self.affiliate1 = self.create_affiliate(user1)
        self.affiliate2 = self.create_affiliate(user2)
        self.commision = self.create_comission(affiliate=self.affiliate1)
        
    def test_list_view_custom_filters(self):
        """ Validate custom filters in list view """
        
        # Login as admin
        self.client.login(username=self.admin_user, password=self.admin_pass)

        # Open employee list page
        response = self.client.get(self.endpoint)
        soup = BeautifulSoup(response.content, "html.parser")

        # Validate years
        affiliates_names = [self.affiliate1.name, self.affiliate2.name]

        affiliates_options = soup.select('option[data-name="affiliate"]')
        for option in affiliates_options:
            self.assertIn(option.text.strip(), affiliates_names)
    
    
class ComissionAdminUserAffiliateTestCase(TestAffiliatesModelsBase):
    """Test admin views for Comission model as affiliate user"""
    
    pass