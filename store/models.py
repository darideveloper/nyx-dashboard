import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
        return f"{self.num} ({self.price})"

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
        verbose_name = 'Extra'
        verbose_name_plural = 'Extras'


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
    logo = models.ImageField()
    addons = models.ManyToManyField(Addon)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.ForeignKey(
        SaleStatus, on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    def __str__(self):
        return f"{self.id} - ({self.user}) {self.set}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex[:12]
            while Sale.objects.filter(id=self.id).exists():
                self.id = uuid.uuid4().hex[:12]
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
        }
        
        return sale_data

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'