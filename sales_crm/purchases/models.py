from django.db import models
from products.models import Product
from django.core.validators import MinValueValidator
from django.utils import timezone

class Supplier(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم المورد")
    contact = models.CharField(max_length=100, verbose_name="جهة الاتصال")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="هاتف المورد")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردون"

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    ORDER_STATUS = (
        ('draft', 'مسودة'),
        ('approved', 'معتمدة'),
        ('received', 'مستلمة'),
        ('canceled', 'ملغاة'),
    )
    
    PAYMENT_METHODS = (
        ('cash', 'نقدي'),
        ('credit', 'أجل'),
        ('transfer', 'تحويل بنكي'),
        ('apple_pay', 'Apple Pay'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="المورد")
    order_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الطلب")
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='draft', verbose_name="حالة الطلب")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name="طريقة الدفع")
    due_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    transaction_reference = models.CharField(max_length=100, null=True, blank=True, verbose_name="رقم المرجع")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="المبلغ الإجمالي")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "أمر شراء"
        verbose_name_plural = "أوامر الشراء"
        ordering = ['-order_date']

    def __str__(self):
        return f"أمر شراء #{self.id} - {self.supplier.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('purchases:order-detail', args=[str(self.id)])

    def calculate_total(self):
        return sum(item.total_cost for item in self.items.all())

    def save(self, *args, **kwargs):
        if self.pk:
            self.total = self.calculate_total()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items', verbose_name="أمر الشراء")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="الكمية")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="تكلفة الوحدة")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="التكلفة الإجمالية")

    class Meta:
        verbose_name = "بند أمر شراء"
        verbose_name_plural = "بنود أوامر الشراء"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
        self.order.save()

# في ملف purchases/models.py أضف ما يلي:

# تأكد من أن النماذج موجودة كما هي
class PurchaseReturn(models.Model):
    RETURN_STATUS = [
        ('pending', 'قيد المعالجة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('completed', 'مكتمل'),
    ]

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='returns',
        verbose_name="أمر الشراء الأصلي"
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
        verbose_name = "مرتجع شراء"
        verbose_name_plural = "مرتجعات المشتريات"
        ordering = ['-return_date']

    def __str__(self):
        return f"مرتجع شراء #{self.return_number}"

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = self.generate_return_number()
        super().save(*args, **kwargs)

    def generate_return_number(self):
        last_return = PurchaseReturn.objects.last()
        if last_return:
            last_number = int(last_return.return_number.split('#')[-1])
            return f"PRET#{last_number + 1:04d}"
        return "PRET#0001"

    def can_approve(self):
        return self.status == 'pending'


class PurchaseReturnItem(models.Model):
    return_entry = models.ForeignKey(
        PurchaseReturn,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="مرتجع الشراء"
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        verbose_name="بند أمر الشراء"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="الكمية المرتجعة")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="تكلفة الوحدة")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المجموع")
    reason = models.TextField(verbose_name="سبب الإرجاع")

    class Meta:
        verbose_name = "بند مرتجع شراء"
        verbose_name_plural = "بنود مرتجعات المشتريات"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)