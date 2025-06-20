from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from store import models


class SaleModelTest(TestCase):
    """Test custom actions of sale model"""

    def setUp(self):

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com", password="test_password", email="test@gmail.com"
        )

        # Create status with a command
        call_command("apps_loaddata")

        # Get sale data
        set = models.Set.objects.all().first()
        colors_num = models.ColorsNum.objects.all().first()
        color = models.Color.objects.all().first()
        status = models.SaleStatus.objects.get(value="Pending")

        self.sale = models.Sale.objects.create(
            user=self.auth_user,
            set=set,
            colors_num=colors_num,
            color_set=color,
            full_name="test full name",
            country="test country",
            state="test state",
            city="test city",
            postal_code="tets pc",
            street_address="test street",
            phone="test phone",
            total=100,
            status=status,
        )

    def test_create_custom_id(self):
        """Create custom id for sale"""

        # Validate custom id
        self.assertEqual(len(self.sale.id), 12)

    def test_change_status_email(self):
        """Send email to client when change status"""

        # Update sale status
        status_delivered = models.SaleStatus.objects.get(value="Delivered")
        self.sale.status = status_delivered
        self.sale.save()

        # Validate email sent
        self.assertEqual(len(mail.outbox), 1)

        # Validate email content
        subject = f"Order {self.sale.id} {status_delivered.value}"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        cta_link_base = f"{settings.HOST}/admin/"
        self.assertIn(cta_link_base, email_html)

    def test_change_status_no_email(self):
        """Status change email not sent because of a excluded status"""

        # Update sale status
        status_excluded = models.SaleStatus.objects.get(value="Reminder Sent")
        self.sale.status = status_excluded
        self.sale.save()

        # Validate email sent
        self.assertEqual(len(mail.outbox), 0)

    def test_change_status_tracking_number(self):
        """Set status to shipped when tracking number is added"""

        # Add tracking number
        tracking_number = "123456"
        self.sale.tracking_number = tracking_number
        self.sale.save()

        # Validate status
        self.assertEqual(self.sale.status.value, "Shipped")

    def test_send_email_tracking_number(self):
        """Send email when tracking number changes"""

        # Add tracking number
        tracking_number = "123456"
        self.sale.tracking_number = tracking_number
        self.sale.save()

        # Validate status
        self.assertEqual(self.sale.status.value, "Shipped")

        # Validate email content
        subject = f"Tracking number added to your order {self.sale.id}"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        cta_link_base = self.sale.tracking_number
        self.assertIn(cta_link_base, email_html)
        self.assertIn(tracking_number, email_html)

    def keep_status_no_email(self):
        """No send email when save sale without status change"""

        self.sale.save()

        # Validate email sent
        self.assertEqual(len(mail.outbox), 0)
