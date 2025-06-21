from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from .models import Sale, SaleItem, Return, ReturnItem
from .forms import SaleForm, SaleItemForm, ReturnForm
from products.models import Product
import json

class SaleListView(ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_queryset(self):
        return Sale.objects.all().order_by('-sale_date')

class SaleDetailView(DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

def get_product_info(request):
    product_id = request.GET.get('product_id')
    product = Product.objects.get(pk=product_id)
    return JsonResponse({
        'price': float(product.price),
        'available_quantity': product.quantity,
    })

def generate_invoice_number():
    last_sale = Sale.objects.last()
    if last_sale:
        last_number = int(last_sale.invoice_number.split('#')[-1])
        return f"INV#{last_number + 1:04d}"
    return "INV#0001"

@transaction.atomic
def create_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.invoice_number = generate_invoice_number()
            
            if sale.customer:
                sale.customer_name = sale.customer.name
                sale.customer_phone = sale.customer.phone
                sale.customer_address = sale.customer.address
            
            subtotal = 0
            products = request.POST.getlist('product')
            quantities = request.POST.getlist('quantity')
            
            sale_items = []
            for product_id, quantity in zip(products, quantities):
                product = Product.objects.get(pk=product_id)
                quantity_int = int(quantity)
                item_total = quantity_int * product.price
                subtotal += item_total
                
                sale_items.append(SaleItem(
                    sale=sale,
                    product=product,
                    quantity=quantity_int,
                    unit_price=product.price,
                    total_price=item_total
                ))
            
            sale.total_amount = subtotal - sale.discount
            sale.save()
            
            for item in sale_items:
                item.save()
                product = item.product
                product.quantity -= item.quantity
                product.save()

            messages.success(request, 'تم حفظ الفاتورة بنجاح!')
            return redirect('sales:sale-detail', pk=sale.pk)
    else:
        form = SaleForm()

    return render(request, 'sales/sale_form.html', {
        'form': form,
        'products': Product.objects.filter(quantity__gt=0),
    })

@transaction.atomic
def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    sale_items = sale.items.all()
    
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            with transaction.atomic():
                for item in sale_items:
                    product = item.product
                    product.quantity += item.quantity
                    product.save()
                
                sale_items.delete()
                
                subtotal = 0
                products = request.POST.getlist('product')
                quantities = request.POST.getlist('quantity')
                
                if not products:
                    messages.error(request, 'يجب إضافة بند واحد على الأقل للفاتورة')
                    return redirect('sales:sale-edit', pk=pk)
                
                for product_id, quantity in zip(products, quantities):
                    if not product_id:
                        continue
                    
                    try:
                        product = Product.objects.get(pk=product_id)
                        quantity_int = int(quantity)
                        
                        if quantity_int > product.quantity:
                            messages.error(request, f'الكمية المطلوبة لـ {product.name} غير متوفرة')
                            return redirect('sales:sale-edit', pk=pk)
                        
                        item_total = quantity_int * product.price
                        subtotal += item_total
                        
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity_int,
                            unit_price=product.price,
                            total_price=item_total
                        )
                        
                        product.quantity -= quantity_int
                        product.save()
                        
                    except (Product.DoesNotExist, ValueError):
                        messages.error(request, 'حدث خطأ في معالجة أحد المنتجات')
                        return redirect('sales:sale-edit', pk=pk)
                
                if sale.customer:
                    sale.customer_name = sale.customer.name
                    sale.customer_phone = sale.customer.phone
                    sale.customer_address = sale.customer.address
                
                sale.total_amount = subtotal - sale.discount
                sale.save()
                
                messages.success(request, 'تم تحديث الفاتورة بنجاح!')
                return redirect('sales:sale-detail', pk=sale.pk)
    else:
        form = SaleForm(instance=sale)
    
    return render(request, 'sales/sale_form.html', {
        'form': form,
        'products': Product.objects.filter(quantity__gt=0),
        'sale': sale,
        'sale_items': sale_items,
        'editing': True,
    })

def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'تم حذف الفاتورة بنجاح!')
        return redirect('sales:sale-list')
    
    return render(request, 'sales/sale_confirm_delete.html', {'sale': sale})

class ReturnListView(ListView):
    model = Return
    template_name = 'sales/return_list.html'
    context_object_name = 'returns'
    paginate_by = 20

    def get_queryset(self):
        return Return.objects.all().order_by('-return_date')

class ReturnDetailView(DetailView):
    model = Return
    template_name = 'sales/return_detail.html'
    context_object_name = 'return_entry'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return_entry = self.object
        
        for item in return_entry.items.all():
            returned_qty = ReturnItem.objects.filter(
                sale_item=item.sale_item
            ).exclude(return_entry=return_entry).aggregate(
                total_returned=Sum('quantity')
            )['total_returned'] or 0
            
            item.sale_item.remaining_qty = item.sale_item.quantity - returned_qty
        
        context['return_items'] = return_entry.items.all()
        return context

@transaction.atomic
def create_return(request):
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            return_entry = form.save(commit=False)
            return_entry.status = 'pending'
            
            subtotal = 0
            sale_items = request.POST.getlist('sale_item')
            quantities = request.POST.getlist('quantity')
            reasons = request.POST.getlist('item_reason')
            
            return_items = []
            for item_id, quantity, reason in zip(sale_items, quantities, reasons):
                sale_item = SaleItem.objects.get(pk=item_id)
                quantity_int = int(quantity)
                
                returned_qty = ReturnItem.objects.filter(
                    sale_item=sale_item
                ).aggregate(Sum('quantity'))['quantity__sum'] or 0
                
                max_returnable = sale_item.quantity - returned_qty
                
                if quantity_int > max_returnable:
                    messages.error(request, 
                        f'الكمية المرتجعة لـ {sale_item.product.name} تتجاوز الحد المسموح ({max_returnable})'
                    )
                    return redirect('sales:return-create')
                
                item_total = quantity_int * sale_item.unit_price
                subtotal += item_total
                
                return_items.append(ReturnItem(
                    return_entry=return_entry,
                    sale_item=sale_item,
                    quantity=quantity_int,
                    unit_price=sale_item.unit_price,
                    total_price=item_total,
                    reason=reason
                ))
            
            return_entry.total_amount = subtotal
            return_entry.save()
            
            for item in return_items:
                item.save()
            
            messages.success(request, 'تم إنشاء المرتجع بنجاح!')
            return redirect('sales:return-detail', pk=return_entry.pk)
    else:
        form = ReturnForm()
    
    return render(request, 'sales/return_form.html', {
        'form': form,
        'sales': Sale.objects.all().order_by('-sale_date'),
    })

@transaction.atomic
def approve_return(request, pk):
    return_entry = get_object_or_404(Return, pk=pk)
    
    if not return_entry.can_approve():
        messages.error(request, 'لا يمكن تأكيد هذا المرتجع')
        return redirect('sales:return-detail', pk=pk)
    
    # إضافة الكمية للمخزون
    for item in return_entry.items.all():
        product = item.sale_item.product
        product.quantity += item.quantity
        product.save()
    
    # تحديث حالة المرتجع
    return_entry.status = 'completed'
    return_entry.approved_by = "النظام"  # أو أي قيمة تريدها
    return_entry.approved_at = timezone.now()
    return_entry.save()
    
    messages.success(request, 'تم تأكيد المرتجع بنجاح وتمت إضافة الكمية للمخزون!')
    return redirect('sales:return-detail', pk=pk)

@transaction.atomic
def edit_return(request, pk):
    return_entry = get_object_or_404(Return, pk=pk)
    return_items = return_entry.items.all()
    
    if request.method == 'POST':
        form = ReturnForm(request.POST, instance=return_entry)
        if form.is_valid():
            with transaction.atomic():
                for item in return_items:
                    product = item.sale_item.product
                    product.quantity -= item.quantity
                    product.save()
                
                return_items.delete()
                
                subtotal = 0
                sale_items = request.POST.getlist('sale_item')
                quantities = request.POST.getlist('quantity')
                reasons = request.POST.getlist('item_reason')
                
                for item_id, quantity, reason in zip(sale_items, quantities, reasons):
                    sale_item = SaleItem.objects.get(pk=item_id)
                    quantity_int = int(quantity)
                    
                    returned_qty = ReturnItem.objects.filter(
                        sale_item=sale_item
                    ).exclude(return_entry=return_entry).aggregate(
                        Sum('quantity')
                    )['quantity__sum'] or 0
                    
                    max_returnable = sale_item.quantity - returned_qty
                    
                    if quantity_int > max_returnable:
                        messages.error(request, 
                            f'الكمية المرتجعة لـ {sale_item.product.name} تتجاوز الحد المسموح ({max_returnable})'
                        )
                        return redirect('sales:return-edit', pk=pk)
                    
                    item_total = quantity_int * sale_item.unit_price
                    subtotal += item_total
                    
                    ReturnItem.objects.create(
                        return_entry=return_entry,
                        sale_item=sale_item,
                        quantity=quantity_int,
                        unit_price=sale_item.unit_price,
                        total_price=item_total,
                        reason=reason
                    )
                    
                    product = sale_item.product
                    product.quantity += quantity_int
                    product.save()
                
                return_entry.total_amount = subtotal
                return_entry.save()
                
                messages.success(request, 'تم تحديث المرتجع بنجاح!')
                return redirect('sales:return-detail', pk=return_entry.pk)
    else:
        form = ReturnForm(instance=return_entry)
    
    return render(request, 'sales/return_form.html', {
        'form': form,
        'return_entry': return_entry,
        'return_items': return_items,
        'editing': True,
    })

def delete_return(request, pk):
    return_entry = get_object_or_404(Return, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in return_entry.items.all():
                product = item.sale_item.product
                product.quantity -= item.quantity
                product.save()
            
            return_entry.delete()
            messages.success(request, 'تم حذف المرتجع بنجاح!')
            return redirect('sales:return-list')
    
    return render(request, 'sales/return_confirm_delete.html', {'return_entry': return_entry})

def get_sale_items(request):
    sale_id = request.GET.get('sale_id')
    if not sale_id:
        return JsonResponse({'error': 'sale_id parameter is required'}, status=400)
    
    try:
        items = SaleItem.objects.filter(sale_id=sale_id).select_related('product')
        
        data = [{
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'total_price': float(item.total_price),
            'returned_quantity': item.returnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'max_returnable': item.quantity - (item.returnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0)
        } for item in items if item.quantity > (item.returnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0)]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def sale_details_json(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    
    items = []
    for item in sale.items.all():
        returned_quantity = item.returnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0
        max_returnable = item.quantity - returned_quantity
        
        if max_returnable > 0:
            items.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'returned_quantity': returned_quantity,
                'max_returnable': max_returnable
            })
    
    data = {
        'invoice_number': sale.invoice_number,
        'sale_date': sale.sale_date.strftime("%Y-%m-%d %H:%M"),
        'customer_name': sale.customer_name or '',
        'payment_method': sale.payment_method,
        'payment_method_display': sale.get_payment_method_display(),
        'discount': float(sale.discount),
        'total_amount': float(sale.total_amount),
        'items': items
    }
    
    return JsonResponse(data)
