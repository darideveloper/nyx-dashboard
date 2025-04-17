from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command

from affiliates import models
from core.test_base.test_models import TestAffiliatesModelsBase


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
    
    
class PaymentTestCase(TestAffiliatesModelsBase):
    def setUp(self):
        
        # Load data
        call_command("apps_loaddata")
        
        # Create comission
        self.comission = self.create_comission()
    
    def test_create_completed_payment(self):
        """
        Test the creation of a payment for an affiliate in completed status.
        validate that the affiliate's balance is updated.
        """
        
        before_balance = self.comission.affiliate.balance
        
        # Create a payment for the affiliate
        payment = models.Payment.objects.create(
            affiliate=self.comission.affiliate,
            amount=100.00,
            status="COMPLETED",
        )
        
        # Check if the payment was reduced from the affiliate's balance
        self.assertNotEqual(
            self.comission.affiliate.balance, before_balance
        )
        self.assertEqual(
            self.comission.affiliate.balance, before_balance - payment.amount
        )
        
    def test_change_status_completed_payment(self):
        """
        Test changing the status of a payment to completed.
        Validate that the affiliate's balance is not updated.
        """
        
        before_balance = self.comission.affiliate.balance
        
        # Create a payment for the affiliate
        payment = models.Payment.objects.create(
            affiliate=self.comission.affiliate,
            amount=100.00,
            status="PENDING",
        )
        
        # Change the status of the payment to completed
        payment.status = "COMPLETED"
        payment.save()
        
        # Check if the payment was reduced from the affiliate's balance
        self.assertNotEqual(
            self.comission.affiliate.balance, before_balance
        )
        self.assertEqual(
            self.comission.affiliate.balance, before_balance - payment.amount
        )
        
    def test_changed_status_pending_after_completed_payment(self):
        """
        Test changing the status of a payment to pending after it was completed.
        Validate that the affiliate's balance is updated.
        """
        
        before_balance = self.comission.affiliate.balance
        
        # Create a payment for the affiliate
        payment = models.Payment.objects.create(
            affiliate=self.comission.affiliate,
            amount=100.00,
            status="COMPLETED",
        )
        
        # Change the status of the payment to pending
        payment.status = "PENDING"
        payment.save()
        
        # Check if the payment was reduced from the affiliate's balance
        self.assertEqual(
            self.comission.affiliate.balance, before_balance
        )