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