from django.db import models
from django.contrib.auth.models import AbstractUser

class Customer(models.Model):
    name = models.CharField(max_length=100, verbose_name="الاسم")
    phone = models.CharField(max_length=20, verbose_name="الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
class User(AbstractUser):
    EMPLOYEE_STATUS = (
        ('active', 'على رأس العمل'),
        ('vacation', 'في إجازة'),
        ('resigned', 'مستقيل'),
        ('terminated', 'مفصول'),
    )
    
    EMPLOYEE_ROLES = (
        ('sales', 'بائع'),
        ('purchases', 'مشتريات'),
        ('admin', 'مدير النظام'),
        ('hr', 'موارد بشرية'),
        ('accountant', 'محاسب'),
    )
    
    role = models.CharField(max_length=20, choices=EMPLOYEE_ROLES, verbose_name="الدور")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="الهاتف")
    status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS, default='active', verbose_name="حالة الموظف")
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الراتب الأساسي")
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="بدل السكن")
    transportation_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="بدل النقل")
    joining_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التعيين")
    termination_date = models.DateField(null=True, blank=True, verbose_name="تاريخ إنهاء الخدمة")
    
    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفين"
    
    def __str__(self):
        return self.username

    @property
    def total_salary(self):
        return self.basic_salary + self.housing_allowance + self.transportation_allowance
    
    def is_active_employee(self):
        return self.status == 'active'
    
    # الدوال المساعدة للتحقق من الأدوار
    @property
    def total_salary(self):
        return self.basic_salary + self.housing_allowance + self.transportation_allowance
    
    def is_active_employee(self):
        return self.status == 'active'
    
    # الدوال المساعدة للتحقق من الأدوار
    def is_admin(self):
        return self.role == 'admin'
    
    def is_sales(self):
        return self.role == 'sales'
    
    def is_purchases(self):
        return self.role == 'purchases'
    
    @property
    def is_hr(self):
        return self.role == 'hr'
    
    @property
    def is_accountant(self):
        return self.role == 'accountant'
    
    def is_active_account(self):
        """تحقق إذا كان الحساب نشطاً (غير مستقيل أو مفصول)"""
        return self.status not in ['resigned', 'terminated']