from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Status(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField()
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
        verbose_name = 'Status'
        verbose_name_plural = 'Status'
    
    
class FutureStock(models.Model):
    id = models.AutoField(primary_key=True)
    amount = models.IntegerField()
    datetime = models.DateTimeField()
    added = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        # Localize timezon in spain
        datetime = timezone.localtime(self.datetime).strftime("%Y-%m-%d %H:%M:%S")
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


class Set(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    recommended = models.BooleanField(default=False)
    logos = models.IntegerField()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'
        

class Colors(models.Model):
    id = models.AutoField(primary_key=True)
    num = models.IntegerField()
    price = models.FloatField()
    details = models.TextField()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Set'
        verbose_name_plural = 'Sets'


class Addon(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Extra'
        verbose_name_plural = 'Extras'


class PromoCodes(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255)
    discount = models.FloatField()
    
    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'


class Sale(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    set = models.ForeignKey(Set, on_delete=models.CASCADE)
    colors_num = models.IntegerField()
    color_set = models.ForeignKey(
        Colors,
        on_delete=models.CASCADE,
        related_name='color_set'
    )
    logo_color_1 = models.ForeignKey(
        Colors,
        on_delete=models.CASCADE,
        related_name='logo_color_1'
    )
    logo_color_2 = models.ForeignKey(
        Colors,
        on_delete=models.CASCADE,
        related_name='logo_color_2'
    )
    logo_color_3 = models.ForeignKey(
        Colors,
        on_delete=models.CASCADE,
        related_name='logo_color_3'
    )
    logo = models.ImageField()
    addons = models.ManyToManyField(Addon)
    promo_code = models.ForeignKey(PromoCodes, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)
    street_address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    total = models.FloatField()
    
    def __str__(self):
        return f"{self.id} - ({self.user}) {self.set}"
    
    class Meta:
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'
