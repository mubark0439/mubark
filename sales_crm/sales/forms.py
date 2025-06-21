from django import forms
from .models import Sale, SaleItem, ReturnItem, Return
from products.models import Product
from core.models import Customer

class SaleForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="العميل",
        required=False
    )

    class Meta:
        model = Sale
        fields = ['customer', 'payment_method', 'discount', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SaleItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(quantity__gt=0),
        widget=forms.Select(attrs={'class': 'form-select product-select'}),
        label="المنتج"
    )

    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': 1
            }),
        }

class ReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = ['sale', 'reason', 'notes']
        widgets = {
            'sale': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sale'].queryset = Sale.objects.all().order_by('-sale_date')


class ReturnItemForm(forms.ModelForm):
    class Meta:
        model = ReturnItem
        fields = ['sale_item', 'quantity', 'reason']
        widgets = {
            'sale_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        sale_id = kwargs.pop('sale_id', None)
        super().__init__(*args, **kwargs)
        if sale_id:
            self.fields['sale_item'].queryset = SaleItem.objects.filter(sale_id=sale_id)        