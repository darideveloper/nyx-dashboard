from django.contrib import admin
from store import models


@admin.register(models.Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'created_at', 'updated_at')
    search_fields = ('key', 'value')
    list_filter = ('created_at', 'updated_at')


@admin.register(models.FutureStock)
class FutureStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'datetime', 'added', 'created_at', 'updated_at')
    search_fields = ('amount', 'datetime', 'added')
    list_filter = ('datetime', 'added', 'created_at', 'updated_at')