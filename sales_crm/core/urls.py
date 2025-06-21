from django.urls import path
from .views import (
    dashboard, customer_list, customer_create, customer_detail, customer_update, CustomerDeleteView,
    user_login, user_logout, employee_list, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView  
)

app_name = 'core'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    # مسارات العملاء
    path('customers/', customer_list, name='customer-list'),
    path('customers/create/', customer_create, name='customer-create'),
    path('customers/<int:pk>/', customer_detail, name='customer-detail'),
    path('customers/<int:pk>/update/', customer_update, name='customer-update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer-delete'),
    
    # مسارات الموظفين (للمدير فقط)
    path('employees/', employee_list, name='employee-list'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee-update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),
]