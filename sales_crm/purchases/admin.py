from django.contrib import admin
from .models import Supplier, PurchaseOrder, OrderItem

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'phone', 'email')
    search_fields = ('name', 'contact', 'phone')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status', 'payment_method', 'total')
    list_filter = ('status', 'payment_method', 'supplier')
    search_fields = ('id', 'supplier__name', 'transaction_reference')
    date_hierarchy = 'order_date'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_cost', 'total_cost')
    list_filter = ('order__supplier', 'product')
    search_fields = ('order__id', 'product__name')