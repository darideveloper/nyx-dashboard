from django.test import TestCase
from django.contrib.auth.models import User

from affiliates import models


class AffiliateTestCase(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@gmail.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )
        
        self.affiliate = models.Affiliate.objects.create(
            user=self.user,
            social_media="https://instagram.com/testuser",
            promo_code="TEST123",
            balance=100.00,
        )

    def test_name(self):
        """Test the name property of the Affiliate model (uses user data)"""
        self.assertEqual(self.affiliate.name, self.user.get_full_name())
        
    def test_email(self):
        """Test the email property of the Affiliate model (uses user data)"""
        self.assertEqual(self.affiliate.email, self.user.email)
        
    def test_active(self):
        """Test the active property of the Affiliate model (uses user data)"""
        self.assertTrue(self.affiliate.active)
        
    def test_active_false(self):
        """Test the active property of the Affiliate model (uses user data)"""
        self.user.is_active = False
        self.user.save()
        self.assertFalse(self.affiliate.active)
        