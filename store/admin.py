import openpyxl

from django.contrib import admin
from django.http import HttpResponse

from store import models
from utils.admin import is_user_admin


def export_sale_to_excel(modelSale, request, queryset):
    """ Export sales to Excel """
    
    # Create a new workbook
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Sales'
    
    # Save sales header
    header = [
        "id",
        "estado",
        "fecha",
        "precio",
        "email",
        "set",
        "país",
        "persona",
        "comentarios",
        "link",
    ]
    
    worksheet.append(header)
    
    # Get sales data
    for sale in queryset:
        
        data = sale.get_sale_data_list()
        worksheet.append(data)
        
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=export.xlsx'
    workbook.save(response)

    return response


export_sale_to_excel.short_description = 'Export selected to Excel'


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
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('active', 'notified', 'created_at', 'updated_at')


@admin.register(models.SaleStatus)
class SaleStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'value',)
    ordering = ('id',)


@admin.register(models.Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'recommended', 'logos', 'points')
    search_fields = ('name', 'price', 'recommended', 'logos', 'points')
    list_filter = ('recommended', 'logos', 'points')


@admin.register(models.ColorsNum)
class ColorsNumAdmin(admin.ModelAdmin):
    list_display = ('num', 'price', 'details')
    search_fields = ('num', 'price', 'details')
    ordering = ('num',)
    
    
@admin.register(models.Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)
    

@admin.register(models.Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name', 'price')


@admin.register(models.PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'type')
    search_fields = ('code', 'discount', 'type__name')


@admin.register(models.PromoCodeType)
class PromoCodeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    

@admin.register(models.Sale)
class SaleAdmin(admin.ModelAdmin):
    actions = [export_sale_to_excel]
    list_display = ('id', 'user', 'set', 'colors_num', 'total', 'promo_code', 'status',
                    'created_at', 'updated_at')
    search_fields = ('id', 'user__email', 'tracking_number', 'set__name',
                     'colors_num__num', 'addons__name', 'promo_code__code',
                     'full_name', 'country', 'state', 'city', 'postal_code',
                     'street_address', 'phone', 'comments')
    list_filter = ('status', 'created_at', 'updated_at', "user", "set", "colors_num",
                   "color_set", "logo_color_1", "logo_color_2", "logo_color_3",
                   "addons", "promo_code", "country", "state", 'reminders_sent')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
            
        # Get admin type
        user_auth = request.user
        
        # Validte if user is in "admins" group
        user_admin = is_user_admin(request.user)
                    
        if not user_admin:
            
            # Filter instructions by user
            return models.Sale.objects.filter(user=user_auth)
            
        # Render all instructions
        return models.Sale.objects.all()