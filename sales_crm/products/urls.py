from django.urls import path
from .views import (
    ProductListView, product_create, product_update, ProductDeleteView,
    CategoryListView, category_create, category_update, CategoryDeleteView,
    product_detail, get_product_price, OutOfStockListView
)
from django.conf import settings
from django.conf.urls.static import static

app_name = 'products'

urlpatterns = [
    # مسارات المنتجات
    path('<int:pk>/', product_detail, name='product-detail'),
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', product_create, name='product-create'),
    path('<int:pk>/update/', product_update, name='product-update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('<int:pk>/price/', get_product_price, name='product-price'),
    path('out-of-stock/', OutOfStockListView.as_view(), name='out-of-stock'),
    
    # مسارات الفئات
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', category_create, name='category-create'),
    path('categories/<int:pk>/update/', category_update, name='category-update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
]