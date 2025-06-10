import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

import pytz

from utils.emails import send_email


class FutureStock(models.Model):
    id = models.AutoField(primary_key=True)
    amount = models.IntegerField()
    datetime = models.DateTimeField()
    added = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Localize timezon in spain
        datetime = timezone.localtime(
            self.datetime).strftime("%Y-%m-%d %H:%M:%S")
        return f"({self.amount}) {datetime}"

    class Meta:
        verbose_name = 'Future Stock'
        verbose_name_plural = 'Future Stocks'


class FutureStockSubscription(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    future_stock = models.ForeignKey(FutureStock, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"({self.user}) {self.future_stock}"

    class Meta:
        verbose_name = 'Future Stock Subscription'
        verbose_name_plural = 'Future Stock Subscriptions'


class StoreStatus(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_readonly_fields(self, request, obj=None):
        # No edit key after creation
        if obj:
            return ['key']
        else:
            return []

    def __str__(self):
        return f"({self.key}) {self.value}"

    class Meta:
        verbose_name = 'Store status'
        verbose_name_plural = 'Store status'


class SaleStatus(models.Model):
    id = models.AutoField(primary_key=True)
    value = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = 'Sale status'
        verbose_name_plural = 'Sale status'


class Set(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    price = models.FloatField()
    recommended = models.BooleanField(default=False)
    logos = models.IntegerField()
    points = models.IntegerField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'


class ColorsNum(models.Model):
    id = models.AutoField(primary_key=True)
    num = models.IntegerField(unique=True)
    price = models.FloatField()
    details = models.TextField()

    def __str__(self):
        return self.details

    class Meta:
        verbose_name = 'Colors Num'
        verbose_name_plural = 'Colors Num'


class Color(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Color'
        verbose_name_plural = 'Colors'


class Addon(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    price = models.FloatField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Addon'
        verbose_name_plural = 'Addons'


class PromoCodeType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Promo Code Type'
        verbose_name_plural = 'Promo Code Types'


class PromoCode(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True)
    discount = models.FloatField()
    type = models.ForeignKey(PromoCodeType, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.code

    class Meta:
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'


class Sale(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=32,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    set = models.ForeignKey(Set, on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=255, null=True, blank=True)
    colors_num = models.ForeignKey(ColorsNum, on_delete=models.CASCADE)
    color_set = models.ForeignKey(
        Color, on_delete=models.SET_NULL,
        related_name='color_set', null=True,
    )
    logo_color_1 = models.ForeignKey(
        Color, on_delete=models.SET_NULL,
        related_name='logo_color_1', null=True, blank=True,
    )
    logo_color_2 = models.ForeignKey(
        Color, on_delete=models.SET_NULL,
        related_name='logo_color_2', null=True, blank=True,
    )
    logo_color_3 = models.ForeignKey(
        Color, on_delete=models.SET_NULL,
        related_name='logo_color_3', null=True, blank=True,
    )
    logo = models.ImageField(null=True, blank=True, upload_to='logos/')
    addons = models.ManyToManyField(Addon, blank=True)
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    full_name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    total = models.FloatField()
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(editable=True)
    updated_at = models.DateTimeField(editable=True)
    status = models.ForeignKey(
        SaleStatus, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    reminders_sent = models.IntegerField(default=0)
    payment_link = models.CharField(max_length=255, null=True, blank=True)
    invoice_file = models.FileField(upload_to="invoice_files")

    def __str__(self):
        return f"{self.id} - ({self.user}) {self.set}"

    def save(self, *args, **kwargs):

        if not self.id:
            # Set created at
            self.created_at = timezone.now()

            # Custom id
            self.id = uuid.uuid4().hex[:12]
            while Sale.objects.filter(id=self.id).exists():
                self.id = uuid.uuid4().hex[:12]

        # Set updated at
        self.updated_at = timezone.now()

        # Update status if tracking_number is set
        if self.tracking_number and self.status not in ["Shipped", "Delivered"]:
            self.status = SaleStatus.objects.get(value="Shipped")

        sale_old = Sale.objects.filter(id=self.id)
        if sale_old:
            sale_old = sale_old.first()

            # Send email if tracking number has been changed
            if sale_old.tracking_number != self.tracking_number:
                send_email(
                    subject=f"Tracking number added to your order {self.id}",
                    first_name=self.user.first_name,
                    last_name=self.user.last_name,
                    texts=[
                        f'Your tracking number has been added to your order {self.id}',
                        f'Your tracking: {self.tracking_number}',
                    ],
                    cta_link=self.tracking_number,
                    cta_text="Track your order",
                    to_email=self.user.email,
                )

            # Send email to user when status change
            valid_status = [
                "Manufacturing",
                "Shipped",
                "Delivered",
            ]
            if self.status and sale_old.status != self.status \
                    and self.status.value in valid_status:

                send_email(
                    subject=f"Order {self.id} {self.status.value}",
                    first_name=self.user.first_name,
                    last_name=self.user.last_name,
                    texts=[
                        f'Your order status has been changed to "{
                            self.status.value}"'
                    ],
                    cta_link=f"{settings.HOST}/admin/",
                    cta_text="View order in Dashboard",
                    to_email=self.user.email,
                )

        super(Sale, self).save(*args, **kwargs)

    def get_sale_data_dict(self) -> dict:
        """ Return sale summary data as dictionary

        Returns:
            dict: Sale summary data
        """

        addons_objs = self.addons.all()
        addons = ", ".join([addon.name for addon in addons_objs])

        sale_data = {
            "Order Number": self.id,
            "Email": self.user.email,
            "Set": str(self.set),
            "Colors Number": self.colors_num.details,
            "Color Set": self.color_set.name,
            "Logo color 1": self.logo_color_1.name if self.logo_color_1 else "",
            "Logo color 2": self.logo_color_2.name if self.logo_color_2 else "",
            "Logo color 3": self.logo_color_3.name if self.logo_color_3 else "",
            "Addons/Extras": addons,
            "Promo Code": self.promo_code.code if self.promo_code else "",
            "Full Name": self.full_name,
            "Country": self.country,
            "State": self.state,
            "City": self.city,
            "Postal Code": self.postal_code,
            "Street Address": self.street_address,
            "Phone": self.phone,
            "Total": self.total,
            "Comments": self.comments,
        }

        return sale_data

    def get_sale_data_list(self) -> list:
        """ Return sale summary data as list

        Returns:
            list: Sale summary data
                id
                status__value
                created_at
                total
                user__email
                set__name
                country
                personal_info (client name, country, state, city,
                postal code, street address, phone)
                comments
                admin link
                
        """
        
        # Format personal info
        personal_info = f"\nNombre: {self.full_name}"
        personal_info += f"\nPaís: {self.country}"
        personal_info += f"\nEstado: {self.state}"
        personal_info += f"\nCiudad: {self.city}"
        personal_info += f"\nCódigo Postal: {self.postal_code}"
        personal_info += f"\nDirección: {self.street_address}"
        personal_info += f"\nTeléfono: {self.phone}"
        
        # Parse created at to spian timezone
        time_zone_str = settings.TIME_ZONE
        time_zone = pytz.timezone(time_zone_str)
        created_at = self.created_at.astimezone(time_zone)
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
        
        # Merge all data
        data = [
            self.id,
            self.status.value,
            created_at_str,
            self.total,
            self.user.email,
            self.set.name,
            self.country,
            personal_info,
            self.comments if self.comments else "",
            f"{settings.HOST}/admin/store/sale/{self.id}/change/",
        ]
        
        return data

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
