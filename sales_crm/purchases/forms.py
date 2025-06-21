from django import forms
from .models import (
    # الواردات الأصلية
    PurchaseOrder, OrderItem, Supplier,
    
    # النماذج الجديدة لمرتجعات المشتريات
    PurchaseReturn, PurchaseReturnItem
)
from django.forms import inlineformset_factory

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'payment_method', 'due_date', 'transaction_reference', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_payment_method'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'id': 'id_due_date',
                'type': 'date'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_transaction_reference'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    class Media:
        js = ('js/purchase_order.js',)

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_cost']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select product-select',
                'onchange': 'getProductCost(this)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity',
                'min': '1',
                'oninput': 'calculateTotal(this)'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control unit-cost',
                'step': '0.01',
                'oninput': 'calculateTotal(this)'
            }),
        }

OrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# في ملف purchases/forms.py أضف ما يلي:

class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturn
        fields = ['purchase_order', 'reason', 'notes']
        widgets = {
            'purchase_order': forms.Select(attrs={'class': 'form-select', 'id': 'id_purchase_order'}),  # ✅ التعديل هنا
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purchase_order'].queryset = PurchaseOrder.objects.all().order_by('-order_date')


class PurchaseReturnItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnItem
        fields = ['order_item', 'quantity', 'reason']
        widgets = {
            'order_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        order_id = kwargs.pop('order_id', None)
        super().__init__(*args, **kwargs)
        if order_id:
            self.fields['order_item'].queryset = OrderItem.objects.filter(order_id=order_id)        