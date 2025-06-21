from django.contrib import admin
from .models import Category, Product

class InStockFilter(admin.SimpleListFilter):
    """فلتر مخصص لحالة التوفر"""
    title = 'حالة التوفر'
    parameter_name = 'in_stock'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'متوفر'),
            ('no', 'غير متوفر'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(quantity__gt=0)
        if self.value() == 'no':
            return queryset.filter(quantity=0)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_per_page = 20

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'quantity', 'in_stock_display')
    list_filter = ('category', InStockFilter)  # استخدام الفلتر المخصص بدلاً من property
    search_fields = ('name', 'barcode', 'description')
    list_per_page = 20
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'category', 'description')
        }),
        ('المعلومات المالية', {
            'fields': ('price', 'cost')
        }),
        ('المخزون', {
            'fields': ('quantity', 'barcode')
        }),
    )
    
    def in_stock_display(self, obj):
        return obj.in_stock
    in_stock_display.boolean = True
    in_stock_display.short_description = 'متوفر'