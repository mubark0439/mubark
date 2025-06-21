from django.db import models
from django.core.validators import MinValueValidator
from products.models import Product
from core.models import Customer

class Sale(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الفاتورة")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="العميل"
    )
    customer_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="اسم العميل")
    customer_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="هاتف العميل")
    customer_address = models.TextField(blank=True, null=True, verbose_name="عنوان العميل")
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="الخصم")
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'نقدي'),
            ('card', 'بطاقة ائتمان'),
            ('bank', 'تحويل بنكي'),
        ],
        default='cash',
        verbose_name="طريقة الدفع"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "فاتورة بيع"
        verbose_name_plural = "فواتير البيع"
        ordering = ['-sale_date']

    def __str__(self):
        return f"فاتورة #{self.invoice_number}"

    def save(self, *args, **kwargs):
        if self.customer:
            self.customer_name = self.customer.name
            self.customer_phone = self.customer.phone
            self.customer_address = self.customer.address
        super().save(*args, **kwargs)

    def get_subtotal(self):
        return sum(item.total_price for item in self.items.all())

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name="الفاتورة")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="الكمية")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المجموع")

    class Meta:
        verbose_name = "بند بيع"
        verbose_name_plural = "بنود البيع"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Return(models.Model):
    RETURN_STATUS = [
        ('pending', 'قيد المعالجة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('completed', 'مكتمل'),
    ]

    sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        related_name='returns',
        verbose_name="الفاتورة الأصلية"
    )
    return_date = models.DateTimeField(auto_now_add=True)
    return_number = models.CharField(max_length=50, unique=True, verbose_name="رقم المرتجع")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="المبلغ المسترجع")
    reason = models.TextField(verbose_name="سبب الإرجاع")
    status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS,
        default='pending',
        verbose_name="حالة المرتجع"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    approved_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="تم التاكيد بواسطة"
    )

    class Meta:
        verbose_name = "مرتجع"
        verbose_name_plural = "المرتجعات"
        ordering = ['-return_date']

    def __str__(self):
        return f"مرتجع #{self.return_number}"

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = self.generate_return_number()
        super().save(*args, **kwargs)

    def generate_return_number(self):
        last_return = Return.objects.last()
        if last_return:
            last_number = int(last_return.return_number.split('#')[-1])
            return f"RET#{last_number + 1:04d}"
        return "RET#0001"

    def can_approve(self):
        return self.status == 'pending'

class ReturnItem(models.Model):
    return_entry = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="المرتجع"
    )
    sale_item = models.ForeignKey(
        SaleItem,
        on_delete=models.PROTECT,
        verbose_name="بند البيع"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="الكمية المرتجعة")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المجموع")
    reason = models.TextField(verbose_name="سبب الإرجاع")

    class Meta:
        verbose_name = "بند مرتجع"
        verbose_name_plural = "بنود المرتجعات"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)