from django.urls import path
from . import views
from .views import (
    # الواردات الأصلية
    PurchaseOrderListView, PurchaseOrderCreateView, PurchaseOrderDetailView,
    PurchaseOrderUpdateView, PurchaseOrderDeleteView,
    SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView,
    get_product_cost, receive_order,
    
    # الواردات الجديدة لمرتجعات المشتريات
    PurchaseReturnListView, PurchaseReturnDetailView,
    create_purchase_return, edit_purchase_return, delete_purchase_return,
    approve_purchase_return, get_order_items, order_details_json
)

app_name = 'purchases'

urlpatterns = [
    # Purchase Orders
    path('', PurchaseOrderListView.as_view(), name='purchases-home'),
    path('orders/', PurchaseOrderListView.as_view(), name='order-list'),
    path('orders/create/', PurchaseOrderCreateView.as_view(), name='order-create'),
    path('orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/update/', PurchaseOrderUpdateView.as_view(), name='order-update'),
    path('orders/<int:pk>/delete/', PurchaseOrderDeleteView.as_view(), name='order-delete'),
    path('orders/<int:pk>/receive/', receive_order, name='order-receive'),
    
    # Suppliers
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier-create'),
    path('suppliers/<int:pk>/update/', SupplierUpdateView.as_view(), name='supplier-update'),
    path('suppliers/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier-delete'),

    # Purchase Returns
    path('returns/', PurchaseReturnListView.as_view(), name='return-list'),
    path('returns/create/', create_purchase_return, name='return-create'),
    path('returns/<int:pk>/', PurchaseReturnDetailView.as_view(), name='return-detail'),
    path('returns/<int:pk>/edit/', edit_purchase_return, name='return-edit'),
    path('returns/<int:pk>/delete/', delete_purchase_return, name='return-delete'),
    path('returns/<int:pk>/approve/', approve_purchase_return, name='return-approve'),
    path('get-order-items/', get_order_items, name='get-order-items'),
    path('order-details-json/<int:pk>/', order_details_json, name='order-details-json'),
]