import os
import json
import base64
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from store import models
import PyPDF2
import locale


class SaleViewTestMixin:

    def setUp(self):
        """Create initial data"""

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com", password="test_password", email="test@gmail.com"
        )

        self.endpoint = "/api/store/sale/"

        # Create initial data
        call_command("apps_loaddata")

        # Initial data
        self.data = {
            "email": self.auth_user.email,
            "set": "basic",
            "colors_num": 4,
            "set_color": "blue",
            "logo_color_1": "white",
            "logo_color_2": "red",
            "logo_color_3": "blue",
            "logo": "",
            "included_extras": [
                "Straps",
                "Wifi 2.4ghz USB Dongle",
            ],
            "promo": {
                "code": "sample-promo",
                "discount": {"type": "amount", "value": 100},
            },
            "full_name": "dari",
            "country": "dev",
            "state": "street",
            "city": "ags",
            "postal_code": "20010",
            "street_address": "street 1",
            "phone": "12323123",
            "comments": "test comments",
        }

        # Files paths
        current_path = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.dirname(current_path)
        self.test_files_folder = os.path.join(app_path, "test_files")

        # Add current stock to store status
        self.current_stock = models.StoreStatus.objects.get(key="current_stock")
        self.current_stock.value = 100
        self.current_stock.save()

    @property
    def payment_link_domain(self):
        raise NotImplementedError("Subclasses must define payment_link_domain")

    def __get_logo_base64__(self, file_name: str) -> str:
        """Get logo in base64 string

        Args:
            file_name (str): File namw inside test_files folder

        Returns:
            str: Base64 string
        """

        logo_path = os.path.join(self.test_files_folder, file_name)
        with open(logo_path, "rb") as file:
            logo_data = file.read()
            return base64.b64encode(logo_data).decode("utf-8")

    def test_sale_missing_fields(self):
        """Save new sale but with missing fields"""

        # Missing fields
        data = {"test": "test"}
        json_data = json.dumps(data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # First missing field detected
        self.assertEqual(res.json()["message"], "Missing field: email")

    def test_sale_no_logo(self):
        """Save new sale with full data but without logo"""

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        json_res = res.json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_res["message"], "Sale saved")

        # Validate stripe link
        self.assertTrue(json_res["data"]["payment_link"])
        self.assertTrue(self.payment_link_domain in json_res["data"]["payment_link"])

        # Validate colors
        colors = {
            "set_color": self.data["set_color"],
            "logo_color_1": self.data["logo_color_1"],
            "logo_color_2": self.data["logo_color_2"],
            "logo_color_3": self.data["logo_color_3"],
        }
        colors_objs = {}
        for color_key, color_value in colors.items():
            color_obj = models.Color.objects.filter(name=color_value)
            self.assertEqual(color_obj.count(), 1)
            colors_objs[color_key] = color_obj[0]

        # Validate promo type
        promo_data = self.data["promo"]
        promo_type = promo_data["discount"]["type"]
        promo_type_obj = models.PromoCodeType.objects.filter(name=promo_type)
        self.assertEqual(promo_type_obj.count(), 1)
        self.assertEqual(promo_type_obj[0].name, promo_type)

        # Validate promo (no auto created)
        promo_data = self.data["promo"]
        promo_obj = models.PromoCode.objects.filter(code=promo_data["code"])
        self.assertEqual(promo_obj.count(), 0)

        # Validate sale data
        sale_obj = models.Sale.objects.all()
        self.assertEqual(sale_obj.count(), 1)
        self.assertEqual(sale_obj[0].user, self.auth_user)
        self.assertEqual(sale_obj[0].set.name, self.data["set"])
        self.assertEqual(sale_obj[0].colors_num.num, self.data["colors_num"])
        self.assertEqual(sale_obj[0].color_set, colors_objs["set_color"])
        self.assertEqual(sale_obj[0].logo_color_1, colors_objs["logo_color_1"])
        self.assertEqual(sale_obj[0].logo_color_2, colors_objs["logo_color_2"])
        self.assertEqual(sale_obj[0].logo_color_3, colors_objs["logo_color_3"])
        self.assertEqual(sale_obj[0].logo, "")
        self.assertEqual(sale_obj[0].promo_code, None)
        self.assertEqual(sale_obj[0].full_name, self.data["full_name"])
        self.assertEqual(sale_obj[0].country, self.data["country"])
        self.assertEqual(sale_obj[0].state, self.data["state"])
        self.assertEqual(sale_obj[0].city, self.data["city"])
        self.assertEqual(sale_obj[0].postal_code, self.data["postal_code"])
        self.assertEqual(sale_obj[0].street_address, self.data["street_address"])
        self.assertEqual(sale_obj[0].phone, self.data["phone"])
        self.assertEqual(sale_obj[0].status.value, "Pending")

        # Validate total
        total = 0
        set_obj = models.Set.objects.filter(name=self.data["set"]).first()
        colors_num_obj = models.ColorsNum.objects.filter(
            num=self.data["colors_num"]
        ).first()
        addons = models.Addon.objects.filter(name__in=self.data["included_extras"])
        total += set_obj.price
        total += colors_num_obj.price
        for addon in addons:
            total += addon.price
        total = round(total, 2)
        self.assertEqual(sale_obj[0].total, total)

        # Validte empty logo
        self.assertEqual(sale_obj[0].logo, "")

    def test_logo_png(self):
        """Save sale with a logo in png"""

        image_base64 = "data:image/png;base64,"
        image_base64 += self.__get_logo_base64__("logo.png")

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate logo file
        sale = models.Sale.objects.all()[0]
        self.assertTrue(sale.logo.url)

    def test_logo_svg(self):
        """Save sale with a logo in svg"""

        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += self.__get_logo_base64__("logo.svg")

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate logo file
        sale = models.Sale.objects.all()[0]
        self.assertTrue(sale.logo.url)

    def test_logo_jpg(self):
        """Save sale with a logo in jpg
        Expect to fail because jpg is not allowed
        """

        image_base64 = "data:image/jpg;base64,"
        image_base64 += self.__get_logo_base64__("logo.jpg")

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # Validate No logo file
        sale = models.Sale.objects.all()[0]
        self.assertFalse(sale.logo)

        # Validate error response
        self.assertEqual(res.json()["status"], "error")
        self.assertEqual(res.json()["message"], "Invalid logo format")
        self.assertEqual(res.json()["data"], {})

    def test_invalid_logo(self):
        """Save sale with a logo in svg broken
        Expect to fail because svg base64 is broken
        """

        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += "invalid string"

        # Add logo to data
        self.data["logo"] = image_base64

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # Validate sale deleted
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 0)

        # Validate error response
        self.assertEqual(res.json()["status"], "error")
        self.assertEqual(res.json()["message"], "Error saving logo")
        self.assertEqual(res.json()["data"], {})

    def test_1_colors(self):
        """Save sale with single color (set color)"""

        # Change colors num to 1
        self.data["colors_num"] = 1

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1, None)
        self.assertEqual(sale.logo_color_2, None)
        self.assertEqual(sale.logo_color_3, None)

    def test_2_color(self):
        """Save sale with set color and 1 logo color"""

        # Change colors num to 1
        self.data["colors_num"] = 2

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2, None)
        self.assertEqual(sale.logo_color_3, None)

    def test_3_color(self):
        """Save sale with set color and 2 logo colors"""

        # Change colors num to 1
        self.data["colors_num"] = 3

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3, None)

    def test_4_color(self):
        """Save sale with set color and 3 logo colors"""

        # Change colors num to 1
        self.data["colors_num"] = 4

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate sale data
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3.name, self.data["logo_color_3"])

    def test_guest_user(self):
        """Save new sale with a guest user"""

        # Delete old sales
        models.Sale.objects.all().delete()

        self.data["email"] = "guest_user@gmail.com"

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Sale saved")

        # Validate user created
        users = User.objects.filter(email=self.data["email"])
        self.assertEqual(users.count(), 1)
        user = users[0]
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.username, self.data["email"])
        self.assertEqual(user.email, self.data["email"])

        # Validate invite email sent
        self.assertGreaterEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, "Nyx Trackers Complete your registration")
        self.assertEqual(sent_email.to, [self.data["email"]])

        # Validate email text content
        cta_link_base = f"{settings.HOST}/sign-up/"
        sent_email = mail.outbox[0]
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)
        self.assertIn("Complete registration", email_html)

    def test_no_stock(self):
        """Skip sale when there is no stock"""

        # Logo path
        image_base64 = "data:image/svg+xml;base64,"
        image_base64 += self.__get_logo_base64__("logo.svg")

        # Add logo to data
        self.data["logo"] = image_base64

        # Update stock
        self.current_stock.value = "0"
        self.current_stock.save()

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)
        json_data = res.json()
        self.assertEqual(json_data["message"], "No stock available")
        self.assertEqual(json_data["status"], "error")
        self.assertEqual(json_data["data"], {})

        # Valdiate sale created
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

        # Validate sale content (logo, extras, colors, texts, etc)
        sale = sales[0]
        self.assertEqual(sale.status.value, "Pending")
        self.assertTrue(sale.logo)
        self.assertEqual(sale.addons.count(), 2)
        self.assertEqual(sale.set.name, self.data["set"])
        self.assertEqual(sale.colors_num.num, self.data["colors_num"])
        self.assertEqual(sale.color_set.name, self.data["set_color"])
        self.assertEqual(sale.logo_color_1.name, self.data["logo_color_1"])
        self.assertEqual(sale.logo_color_2.name, self.data["logo_color_2"])
        self.assertEqual(sale.logo_color_3.name, self.data["logo_color_3"])
        self.assertEqual(sale.full_name, self.data["full_name"])
        self.assertEqual(sale.country, self.data["country"])
        self.assertEqual(sale.state, self.data["state"])
        self.assertEqual(sale.city, self.data["city"])
        self.assertEqual(sale.postal_code, self.data["postal_code"])
        self.assertEqual(sale.street_address, self.data["street_address"])
        self.assertEqual(sale.phone, self.data["phone"])
        self.assertEqual(sale.comments, self.data["comments"])

    def test_no_comments(self):
        """Save sale without comments"""

        # Remove comments
        self.data.pop("comments")

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Valdiate sale created
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.comments, "")

    def test_long_comments(self):
        """Save sale without comments"""

        # Remove comments
        self.data["comments"] = "a" * 5000

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Valdiate sale created
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.comments, self.data["comments"])

    def test_pending_sale(self):
        """Try to create new sale when user has a pending sale
        Expect to delete old sale, create new one and send emails
        """

        # Create pending sale
        status = models.SaleStatus.objects.get(value="Pending")
        pending_sale = models.Sale.objects.create(
            user=self.auth_user,
            set=models.Set.objects.all().first(),
            colors_num=models.ColorsNum.objects.all().first(),
            color_set=models.Color.objects.all().first(),
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
        pending_sale_id = pending_sale.id

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate unique sale for the user
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

        # Validate sale created
        sale = sales[0]
        self.assertEqual(sale.status.value, "Pending")

        # Validate 2 emails sent
        self.assertEqual(len(mail.outbox), 2)

        # Validate user email text content
        subject = "Nyx Trackers Sale Updated"
        cta_link = f"{settings.HOST}/sign-up"
        cta_text = "Sign up"
        sent_email = mail.outbox[0]
        send_email_html = sent_email.alternatives[0][0]
        self.assertEqual(sent_email.subject, subject)
        self.assertIn(cta_link, send_email_html)
        self.assertIn(cta_text, send_email_html)

        # Validate admin email
        subject = "Nyx Trackers Sale Updated by User"
        cta_link = f"{settings.HOST}/admin/store/sale/"
        cta_link += "?user__id__exact="
        cta_text = "View sale in dashboard"
        cta_text = "View sale in dashboard"
        sent_email = mail.outbox[1]
        send_email_html = sent_email.alternatives[0][0]
        self.assertEqual(sent_email.subject, subject)
        self.assertIn(cta_link, send_email_html)
        self.assertIn(cta_text, send_email_html)

        # Validate new sale id
        self.assertNotEqual(sale.id, pending_sale_id)

    def test_pending_sale_no_stock(self):
        """Try to create new sale when user has a pending sale and there
        is no stock.
        Expect to delete old sale, create new one and send emails
        """

        # Update stock in system
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock.value = 0
        current_stock.save()

        # Create pending sale
        status = models.SaleStatus.objects.get(value="Pending")
        pending_sale = models.Sale.objects.create(
            user=self.auth_user,
            set=models.Set.objects.all().first(),
            colors_num=models.ColorsNum.objects.all().first(),
            color_set=models.Color.objects.all().first(),
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
        pending_sale_id = pending_sale.id

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 400)

        # Validate unique sale for the user
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

        # Validate sale created
        sale = sales[0]
        self.assertEqual(sale.status.value, "Pending")

        # Validate new sale id
        self.assertNotEqual(sale.id, pending_sale_id)

    def test_many_pending_sale(self):
        """Try to create new sale when user has a many pending sales
        Expect to delete old sales, create a new one
        """

        # Create pending sale
        status = models.SaleStatus.objects.get(value="Pending")
        for _ in range(3):
            models.Sale.objects.create(
                user=self.auth_user,
                set=models.Set.objects.all().first(),
                colors_num=models.ColorsNum.objects.all().first(),
                color_set=models.Color.objects.all().first(),
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

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate unique sale for the user
        sales = models.Sale.objects.all()
        self.assertEqual(sales.count(), 1)

    def test_no_promo_code(self):

        # Delete default promo codes
        models.PromoCode.objects.all().delete()

        # Send data
        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate total
        total = 0
        colors_num_obj = models.ColorsNum.objects.get(id=self.data["colors_num"])
        set_obj = models.Set.objects.get(name=self.data["set"])
        total += colors_num_obj.price
        total += set_obj.price
        extras = models.Addon.objects.filter(name__in=self.data["included_extras"])
        extras_total = sum([extra.price for extra in extras])
        total += extras_total

        # Validate total and promo code
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.promo_code, None)
        self.assertEqual(sale.total, total)

    def test_promo_code_amount(self):

        # Delete default promo codes
        models.PromoCode.objects.all().delete()

        # Create promo code
        promo_code = models.PromoCode.objects.create(
            code="test-promo",
            discount=100,
            type=models.PromoCodeType.objects.get(name="amount"),
        )

        # Add promo code to data
        self.data["promo"]["code"] = promo_code.code
        self.data["promo"]["discount"] = {
            "type": promo_code.type.name,
            "value": promo_code.discount,
        }

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate total
        total = 0
        colors_num_obj = models.ColorsNum.objects.get(id=self.data["colors_num"])
        set_obj = models.Set.objects.get(name=self.data["set"])
        total += colors_num_obj.price
        total += set_obj.price
        extras = models.Addon.objects.filter(name__in=self.data["included_extras"])
        extras_total = sum([extra.price for extra in extras])
        total += extras_total

        # Validate total and promo code
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.promo_code, promo_code)
        self.assertEqual(sale.total, total - promo_code.discount)

    def test_promo_code_percentage(self):

        # Delete default promo codes
        models.PromoCode.objects.all().delete()

        # Create promo code
        promo_code = models.PromoCode.objects.create(
            code="test-promo",
            discount=10,
            type=models.PromoCodeType.objects.get(name="percentage"),
        )

        # Add promo code to data
        self.data["promo"]["code"] = promo_code.code
        self.data["promo"]["discount"] = {
            "type": promo_code.type.name,
            "value": promo_code.discount,
        }

        json_data = json.dumps(self.data)
        res = self.client.post(
            self.endpoint, data=json_data, content_type="application/json"
        )

        # Validate response
        self.assertEqual(res.status_code, 200)

        # Validate total
        total = 0
        colors_num_obj = models.ColorsNum.objects.get(id=self.data["colors_num"])
        set_obj = models.Set.objects.get(name=self.data["set"])
        total += colors_num_obj.price
        total += set_obj.price
        extras = models.Addon.objects.filter(name__in=self.data["included_extras"])
        extras_total = sum([extra.price for extra in extras])
        total += extras_total

        # Validate total and promo code
        sale = models.Sale.objects.all()[0]
        self.assertEqual(sale.promo_code, promo_code)
        self.assertEqual(sale.total, total * (1 - promo_code.discount / 100))


class SaleDoneViewTestMixin:

    def setUp(self):
        """Create initial data"""

        # Auth user
        self.auth_user = User.objects.create_user(
            username="test@gmail.com",
            password="test_password",
            email="test@gmail.com",
        )

        # Create initial data
        call_command("apps_loaddata")

        # Create sale
        set = models.Set.objects.all().first()

        colors_num = models.ColorsNum.objects.all().first()

        color = models.Color.objects.all().first()
        status = models.SaleStatus.objects.get(value="Pending")

        # Files paths
        current_path = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.dirname(current_path)
        test_files_folder = os.path.join(app_path, "test_files")

        logo_path = os.path.join(test_files_folder, "logo.png")

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
            total=510,
            status=status,
        )

        # Add logo to sale
        logo = SimpleUploadedFile(
            name="logo.png",
            content=open(logo_path, "rb").read(),
            content_type="image/png",
        )
        self.sale.logo = logo
        self.sale.save()

        # Request data
        self.endpoint = "/api/store/sale-done"

        # Set current stock to 100
        current_stock = models.StoreStatus.objects.get(key="current_stock")
        current_stock.value = 100
        current_stock.save()

        invoice_num = models.StoreStatus.objects.get(key="invoice_num")
        invoice_num.value = 200
        invoice_num.save()

        self.redirect_page = settings.LANDING_HOST

        # Connect payment provider
        self.payment_linker = self.get_payment_linker()

        # Add payment link to sale
        payment_link = self.payment_linker.get_checkout_link(
            sale_id=self.sale.id,
            title="Nyx Trackers Test Sale",
            price=self.sale.total,
            description="Test sale description",
        )
        self.sale.payment_link = payment_link["self"]
        self.sale.save()

    def get_payment_linker(self):
        raise NotImplementedError

    @property
    def commission_rate(self):
        raise NotImplementedError

    def test_get(self):
        """Validate sale already paid"""

        # Validate sale and force payment validation
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")

        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={self.sale.id}&sale-status=success"
        self.assertEqual(res.url, self.redirect_page)

        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Paid")

    def test_get_no_paid(self):
        """Validate sale not paid"""

        # Validate sale (no force)
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")

        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={self.sale.id}&sale-status=error"
        self.assertEqual(res.url, self.redirect_page)

        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Pending")

    def test_get_invalid_id(self):

        fake_id = "fake-id"
        res = self.client.get(f"{self.endpoint}/{fake_id}/")

        # Validate redirect
        self.assertEqual(res.status_code, 302)
        self.redirect_page += f"?sale-id={fake_id}&sale-status=error"
        self.assertEqual(res.url, self.redirect_page)

        # Valisate sale status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Pending")

    def test_email(self):
        """Validate email sent content after sale confirmation"""

        # Validate redirect
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")
        self.assertEqual(res.status_code, 302)

        # validate activation email sent
        self.assertEqual(len(mail.outbox), 2)

        # Validate email text content
        subject = "Nyx Trackers Payment Confirmation"
        cta_link_base = f"{settings.HOST}/admin/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)

        # Validate admin email

        # Validate email text content
        subject = "Nyx Trackers New Sale"
        cta_link_base = f"{settings.HOST}/admin/store/sale/{self.sale.id}/change/"
        sent_email = mail.outbox[1]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)

        # Validate sale details
        sale_data = self.sale.get_sale_data_dict()
        for sale_key, sale_value in sale_data.items():
            self.assertIn(sale_key, email_html)
            self.assertIn(str(sale_value), email_html)

        # Valdate logo in email
        self.assertIn('id="extra-image"', email_html)

    def test_email_no_logo(self):
        """Validate email sent without logo"""

        # Remove logo from sale
        self.sale.logo = None
        self.sale.save()

        # Validate redirect
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")
        self.assertEqual(res.status_code, 302)

        # validate activation email sent
        self.assertEqual(len(mail.outbox), 2)

        # Validate client email

        # Validate email text content
        subject = "Nyx Trackers Payment Confirmation"
        cta_link_base = f"{settings.HOST}/admin/"
        sent_email = mail.outbox[0]
        self.assertEqual(subject, sent_email.subject)

        # Validate cta html tags
        email_html = sent_email.alternatives[0][0]
        self.assertIn(cta_link_base, email_html)

        # Validate sale details
        sale_data = self.sale.get_sale_data_dict()
        for sale_key, sale_value in sale_data.items():
            self.assertIn(sale_key, email_html)
            self.assertIn(str(sale_value), email_html)

        # Valdate logo in email
        self.assertNotIn('id="extra-image"', email_html)

    def test_invalid_payment_email(self):
        """Validate email sent to client when payment is invalid"""

        # No force test sale (detect invalid payment)
        res = self.client.get(f"{self.endpoint}/{self.sale.id}/")
        self.assertEqual(res.status_code, 302)

        # Validate email sent
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Nyx Trackers Payment Error")
        self.assertEqual(email.to, [self.sale.user.email])
        self.assertIn("There was an error with your payment.", email.body)
        self.assertIn("Your order has not been processed.", email.body)
        self.assertIn("Please try again or contact us for support.", email.body)

    def test_invalid_payment_no_email_status(self):
        """No send status change email when order its invalid"""

        payment_error_status = models.SaleStatus.objects.get(value="Payment Error")
        self.sale.status = payment_error_status
        self.sale.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_invoice_created(self):
        """Validate sale already paid and invoice created"""

        # Get initial invoice_num
        invoice_num = models.StoreStatus.objects.get(key="invoice_num")
        self.assertEqual(int(invoice_num.value), 200)

        # Validate sale and force payment validation
        self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")

        # Validate invoice field no empty
        self.sale.refresh_from_db()
        self.assertNotEqual(self.sale.invoice_file.name, "")
        self.assertTrue(self.sale.invoice_file.name.endswith(".pdf"))

        # Validate store status updated
        invoice_num.refresh_from_db()
        self.assertEqual(int(invoice_num.value), 201)

    def test_invoice_no_created(self):
        """Validate sale not paid and no invoice created"""

        # Validate sale (no force)
        self.client.get(f"{self.endpoint}/{self.sale.id}/")

        # Validate no paid status
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status.value, "Pending")

        # Validate invoice field empty
        self.assertEqual(self.sale.invoice_file.name, "")

        # Validate store status not updated
        invoice_num = models.StoreStatus.objects.get(key="invoice_num")
        self.assertEqual(int(invoice_num.value), 200)

    def test_invoice_content(self):
        """Validate invoice content"""

        # Update invoice amounts to easy calcs
        self.sale.total = 100
        self.sale.save()

        # Validate sale and force payment validation
        self.client.get(f"{self.endpoint}/{self.sale.id}/?use_testing=true")

        # Validate invoice file exists
        self.sale.refresh_from_db()
        self.assertIsNotNone(self.sale.invoice_file)

        # Get incoide file
        pdf_text = ""
        with self.sale.invoice_file.open("rb") as invoice_file:
            reader = PyPDF2.PdfReader(invoice_file)
            pdf_text = reader.pages[0].extract_text()

        # Update locale for date formatting
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

        # Get current invoice_num
        invoice_num_str = models.StoreStatus.objects.get(key="invoice_num").value

        # get and formatd data
        date = timezone.now().strftime("%d de %B de %Y")
        invoice_num = int(invoice_num_str) - 1
        name = self.sale.user.get_full_name()
        city = self.sale.city
        state = self.sale.state
        street = self.sale.street_address
        pc = self.sale.postal_code
        country = self.sale.country
        phone = self.sale.phone
        email = self.sale.user.email
        quantity = 1
        total = self.sale.total
        igi = total * settings.INVOICE_IGI_COMMISSION / 100
        provider_fee = total * self.commission_rate / 100
        base = total - igi - provider_fee
        total_str = f"{total:.2f}USD"
        igi_str = f"{igi:.2f}USD"
        provider_fee_str = f"{provider_fee:.2f}USD"
        base_str = f"{base:.2f}USD"

        # Validate data in PDF
        self.assertIn(date, pdf_text)
        self.assertIn(str(invoice_num), pdf_text)
        self.assertIn(name, pdf_text)
        self.assertIn(city, pdf_text)
        self.assertIn(state, pdf_text)
        self.assertIn(street, pdf_text)
        self.assertIn(pc, pdf_text)
        self.assertIn(country, pdf_text)
        self.assertIn(phone, pdf_text)
        self.assertIn(email, pdf_text)
        self.assertIn(str(quantity), pdf_text)
        self.assertIn(total_str, pdf_text)
        self.assertIn(igi_str, pdf_text)
        self.assertIn(provider_fee_str, pdf_text)
        self.assertIn(base_str, pdf_text)
