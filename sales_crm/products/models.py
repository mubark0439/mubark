from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم الفئة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")

    class Meta:
        verbose_name = "فئة"
        verbose_name_plural = "الفئات"

    def __str__(self):
        return self.name



class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المنتج")
    quantity = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="الفئة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    image = models.ImageField(
        upload_to='media/%Y/%m/%d/',  # تنظيم الملفات في مجلدات حسب التاريخ
        null=True,
        blank=True,
        verbose_name="صورة المنتج",
        help_text="تحميل صورة المنتج (اختياري)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="التكلفة")
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="الكمية المتاحة")
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="باركود")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.price} ريال"

    @property
    def profit(self):
        return self.price - self.cost

    @property
    def in_stock(self):
        return self.quantity > 0
    
    
    