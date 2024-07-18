from django.db import models


class Status(models.Model):
    # No edit key after creation
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
        return f"({self.amount}) {self.datetime}"
    
    class Meta:
        verbose_name = 'Future Stock'
        verbose_name_plural = 'Future Stocks'