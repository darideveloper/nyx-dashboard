from django.contrib import admin
from landing import models


@admin.register(models.category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(models.Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'value', 'link']
    search_fields = ['key', 'category__name', 'value', 'link']
    ordering = ['key']
    
    
@admin.register(models.Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'image']
    search_fields = ['key', 'category__name', 'image']
    ordering = ['key']
    
    change_list_template = 'admin/list_render_media.html'
    
    
@admin.register(models.Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'video']
    search_fields = ['key', 'category__name', 'video']
    ordering = ['key']
    
    change_list_template = 'admin/list_render_media.html'