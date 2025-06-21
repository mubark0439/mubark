from django.urls import path
from .views import (
    SaleListView, SaleDetailView,
    create_sale, get_product_info,
    edit_sale, delete_sale,
    sale_details_json,
    ReturnListView, ReturnDetailView,
    create_return, edit_return, delete_return,
    get_sale_items, approve_return
)

app_name = 'sales'

urlpatterns = [
    path('', SaleListView.as_view(), name='sale-list'),
    path('create/', create_sale, name='sale-create'),
    path('<int:pk>/', SaleDetailView.as_view(), name='sale-detail'),
    path('<int:pk>/edit/', edit_sale, name='sale-edit'),
    path('<int:pk>/delete/', delete_sale, name='sale-delete'),
    path('get-product-info/', get_product_info, name='get-product-info'),
    path('returns/', ReturnListView.as_view(), name='return-list'),
    path('returns/create/', create_return, name='return-create'),
    path('returns/<int:pk>/', ReturnDetailView.as_view(), name='return-detail'),
    path('returns/<int:pk>/edit/', edit_return, name='return-edit'),
    path('returns/<int:pk>/delete/', delete_return, name='return-delete'),
    path('returns/<int:pk>/approve/', approve_return, name='return-approve'),
    path('get-sale-items/', get_sale_items, name='get-sale-items'),
    path('sale-details-json/<int:pk>/', sale_details_json, name='sale-details-json'),
]