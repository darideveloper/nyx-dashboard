from django.core import mail
from django.core.management import call_command

from core.test_base.test_models import TestAffiliatesModelsBase


class AffiliatesPaymentsNotification(TestAffiliatesModelsBase):
    """ Test affiliates_payments_notification command """
    
    def setUp(self):
        
        # Load initial data
        call_command('apps_loaddata')
        
        # Create affiliates with initial positive balances
        self.affiliate = self.create_affiliate(balance=100.00)
        
    def __validate_email__(self, email, affiliate):
        """ Validate email content
        
        Args:
            email (EmailMessage): The email object to validate.
            affiliate (Affiliate): The affiliate object.
        """
               
        self.assertIn(
            f"Payment Notification for {affiliate.name}",
            email.subject
        )
        self.assertIn(
            f"Affiliate ID: {affiliate.id}",
            email.body
        )
        self.assertIn(
            f"Affiliate Name: {affiliate.name}",
            email.body
        )
        self.assertIn(
            f"Affiliate Email: {affiliate.email}",
            email.body
        )
        self.assertIn(
            f"Amount to be paid: {affiliate.balance}",
            email.body
        )
        
        # Validate email cta content
        url_params = {
            "amount": affiliate.balance,
            "affiliate": affiliate.id,
            "status": "COMPLETED"
        }
        cta_link_base = "/admin/affiliates/payment/add/"
        self.assertIn(cta_link_base, email.body)
        for key, value in url_params.items():
            self.assertIn(f"{key}={value}", email.body)
                
    def test_no_affiliates(self):
        """
        Test command when there are no affiliates.
        """
        
        # Delete all affiliates
        self.affiliate.delete()
        
        # Run the command
        call_command('affiliates_payments_notification')
        
        # Validate no emails are sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_single_affiliate_positive_balance(self):
        """
        Test command with a single affiliate.
        """
    
        # Run the command
        call_command('affiliates_payments_notification')
        
        # validate one email is sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Validate email content
        email = mail.outbox[0]
        self.__validate_email__(email, self.affiliate)
            
    def test_single_affiliate_negative_balance(self):
        """
        Test command with a single affiliate with negative balance.
        """
        
        # Update affiliate balance to negative
        self.affiliate.balance = -50.00
        self.affiliate.save()
        
        # Run the command
        call_command('affiliates_payments_notification')
        
        # Validate no emails are sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_single_affiliate_zero_balance_balance(self):
        """
        Test command with a single affiliate with zero balance.
        """
        
        # Update affiliate balance to zero
        self.affiliate.balance = 0.00
        self.affiliate.save()
        
        # Run the command
        call_command('affiliates_payments_notification')
        
        # Validate no emails are sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_single_affiliate_inactive(self):
        """
        Test command with a single inactive affiliate.
        """
        
        # Update affiliate to inactive
        self.affiliate.user.is_active = False
        self.affiliate.user.save()
        
        # Run the command
        call_command('affiliates_payments_notification')
        
        # Validate no emails are sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_multiple_affiliates_positive(self):
        """
        Test command with multiple affiliates.
        """
        
        # Create another affiliate with positive balance
        self.affiliate2 = self.create_affiliate(balance=200.00)
        
        # Run the command
        call_command('affiliates_payments_notification')
        
        # Validate two emails are sent
        self.assertEqual(len(mail.outbox), 2)
        
        # Validate email content for both affiliates
        for affiliate in [self.affiliate, self.affiliate2]:
            email = list(filter(
                lambda email: f"Affiliate ID: {affiliate.id}" in email.body,
                mail.outbox
            ))[0]
            self.__validate_email__(email, affiliate)
        
        
    
