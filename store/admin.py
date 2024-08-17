from django.contrib import admin
from store import models


@admin.register(models.StoreStatus)
class StoreStatusAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'created_at', 'updated_at')
    search_fields = ('key', 'value')
    list_filter = ('created_at', 'updated_at')
    

@admin.register(models.FutureStock)
class FutureStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'datetime',
                    'added', 'created_at', 'updated_at')
    search_fields = ('amount', 'datetime', 'added')
    list_filter = ('datetime', 'added', 'created_at', 'updated_at')


@admin.register(models.FutureStockSubscription)
class FutureStockSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'future_stock', 'active',
                    'notified', 'created_at', 'updated_at')
    search_fields = ('user__email', 'future_stock', 'active', 'notified')
    list_filter = ('active', 'notified', 'created_at', 'updated_at')


@admin.register(models.SaleStatus)
class SaleStatusAdmin(admin.ModelAdmin):
    list_display = ('value',)


@admin.register(models.Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'recommended', 'logos', 'points')
    search_fields = ('name', 'price', 'recommended', 'logos', 'points')
    list_filter = ('recommended', 'logos', 'points')


@admin.register(models.ColorsNum)
class ColorsNumAdmin(admin.ModelAdmin):
    list_display = ('id', 'num', 'price', 'details')
    search_fields = ('num', 'price', 'details')


@admin.register(models.Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name', 'price')


@admin.register(models.PromoCodes)
class PromoCodesAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount')
    search_fields = ('code', 'discount')


@admin.register(models.Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('user', 'set', 'colors_num', 'promo_code', 'status', 'created_at',
                    'updated_at')
    search_fields = ('user__email', 'full_name', 'set__name', 'colors_num__num',
                     'color_set', 'logo_color_1', 'logo_color_2', 'logo_color_3',
                     'addons__name', 'promo_code__code', 'full_name', 'country', 'state',
                     'city', 'postal_code', 'street_address', 'phone')
    list_filter = ('status', 'created_at', 'updated_at', "user", "set", "colors_num",
                   "color_set", "logo_color_1", "logo_color_2", "logo_color_3",
                   "addons", "promo_code", "country", "state")