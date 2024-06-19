from django.contrib import admin
from landing import models


@admin.register(models.Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'link']
    search_fields = ['key', 'value', 'link']
    list_display_links = ['key']