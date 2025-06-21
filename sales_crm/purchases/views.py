# Standard library imports
from datetime import datetime

# Django imports
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum

# Local imports
from .models import Supplier, PurchaseOrder, OrderItem, PurchaseReturn, PurchaseReturnItem
from .forms import PurchaseOrderForm, OrderItemFormSet, SupplierForm, PurchaseReturnForm
from products.models import Product

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchases/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    ordering = ['-order_date']

class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST)
        else:
            context['formset'] = OrderItemFormSet(queryset=OrderItem.objects.none())
        context['products'] = Product.objects.all()
        context['now'] = timezone.now()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            self.object.total = self.object.calculate_total()
            self.object.save()
            
            messages.success(self.request, 'تم إنشاء أمر الشراء بنجاح')
            return redirect(self.get_success_url())
        
        return self.render_to_response(self.get_context_data(form=form))

class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchases/order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = OrderItemFormSet(instance=self.object)
        context['products'] = Product.objects.all()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            self.object.total = self.object.calculate_total()
            self.object.save()
            
            messages.success(self.request, 'تم تحديث أمر الشراء بنجاح')
            return redirect(self.object.get_absolute_url())
        
        return self.render_to_response(self.get_context_data(form=form))

class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'items__product', 
            'supplier',
            'returns'
        )

class PurchaseOrderDeleteView(DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/order_confirm_delete.html'
    success_url = reverse_lazy('purchases:order-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف أمر الشراء بنجاح')
        return super().delete(request, *args, **kwargs)

def get_product_cost(request):
    product_id = request.GET.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    return JsonResponse({'cost': float(product.cost)})

def receive_order(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if order.status != 'received':
        order.status = 'received'
        order.save()
        
        for item in order.items.all():
            if item.product:
                item.product.quantity += item.quantity
                item.product.save()
        
        messages.success(request, 'تم تأكيد استلام الطلبية وتحديث المخزون بنجاح')
    return redirect('purchases:order-detail', pk=order.id)

# Supplier Views
class SupplierListView(ListView):
    model = Supplier
    template_name = 'purchases/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 10

class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchases/supplier_form.html'
    success_url = reverse_lazy('purchases:supplier-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم إضافة المورد بنجاح')
        return super().form_valid(form)

class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchases/supplier_form.html'
    success_url = reverse_lazy('purchases:supplier-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث بيانات المورد بنجاح')
        return super().form_valid(form)

class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'purchases/supplier_confirm_delete.html'
    success_url = reverse_lazy('purchases:supplier-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المورد بنجاح')
        return super().delete(request, *args, **kwargs)

# Purchase Returns Views
class PurchaseReturnListView(ListView):
    model = PurchaseReturn
    template_name = 'purchases/return_list.html'
    context_object_name = 'returns'
    paginate_by = 10
    ordering = ['-return_date']

class PurchaseReturnDetailView(DetailView):
    model = PurchaseReturn
    template_name = 'purchases/return_detail.html'
    context_object_name = 'return_entry'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return_entry = self.object
        
        for item in return_entry.items.all():
            returned_qty = PurchaseReturnItem.objects.filter(
                order_item=item.order_item
            ).exclude(return_entry=return_entry).aggregate(
                total_returned=Sum('quantity')
            )['total_returned'] or 0
            
            item.order_item.remaining_qty = item.order_item.quantity - returned_qty
        
        context['return_items'] = return_entry.items.all()
        return context

@transaction.atomic
def create_purchase_return(request):
    if request.method == 'POST':
        form = PurchaseReturnForm(request.POST)
        if form.is_valid():
            return_entry = form.save(commit=False)
            return_entry.status = 'pending'
            
            subtotal = 0
            order_items = request.POST.getlist('order_item')
            quantities = request.POST.getlist('quantity')
            reasons = request.POST.getlist('item_reason')
            
            return_items = []
            for item_id, quantity, reason in zip(order_items, quantities, reasons):
                order_item = OrderItem.objects.get(pk=item_id)
                quantity_int = int(quantity)
                
                returned_qty = PurchaseReturnItem.objects.filter(
                    order_item=order_item
                ).aggregate(Sum('quantity'))['quantity__sum'] or 0
                
                max_returnable = order_item.quantity - returned_qty
                
                if quantity_int > max_returnable:
                    messages.error(request, 
                        f'الكمية المرتجعة لـ {order_item.product.name} تتجاوز الحد المسموح ({max_returnable})'
                    )
                    return redirect('purchases:return-create')
                
                item_total = quantity_int * order_item.unit_cost
                subtotal += item_total
                
                return_items.append(PurchaseReturnItem(
                    return_entry=return_entry,
                    order_item=order_item,
                    quantity=quantity_int,
                    unit_cost=order_item.unit_cost,
                    total_cost=item_total,
                    reason=reason
                ))
            
            return_entry.total_amount = subtotal
            return_entry.save()
            
            for item in return_items:
                item.save()
            
            messages.success(request, 'تم إنشاء مرتجع الشراء بنجاح!')
            return redirect('purchases:return-detail', pk=return_entry.pk)
    else:
        form = PurchaseReturnForm()
    
    return render(request, 'purchases/return_form.html', {
        'form': form,
        'orders': PurchaseOrder.objects.all().order_by('-order_date'),
    })

@transaction.atomic
def approve_purchase_return(request, pk):
    return_entry = get_object_or_404(PurchaseReturn, pk=pk)
    
    if not return_entry.can_approve():
        messages.error(request, 'لا يمكن تأكيد هذا المرتجع')
        return redirect('purchases:return-detail', pk=pk)
    
    try:
        # خصم الكمية من المخزون
        for item in return_entry.items.all():
            product = item.order_item.product
            product.quantity -= item.quantity
            product.save()
        
        # تحديث حالة المرتجع
        return_entry.status = 'completed'
        
        # استبدال اسم المستخدم بقيمة افتراضية
        return_entry.approved_by = "النظام"  # أو أي قيمة ثابتة تفضلها
        
        return_entry.save()
        
        messages.success(request, 'تم تأكيد مرتجع الشراء بنجاح وتم خصم الكمية من المخزون!')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء التأكيد: {str(e)}')
    
    return redirect('purchases:return-detail', pk=pk)

@transaction.atomic
def edit_purchase_return(request, pk):
    return_entry = get_object_or_404(PurchaseReturn, pk=pk)
    return_items = return_entry.items.all()
    
    if request.method == 'POST':
        form = PurchaseReturnForm(request.POST, instance=return_entry)
        if form.is_valid():
            with transaction.atomic():
                for item in return_items:
                    product = item.order_item.product
                    product.quantity += item.quantity  # استرجاع الكمية التي تم خصمها سابقاً
                    product.save()
                
                return_items.delete()
                
                subtotal = 0
                order_items = request.POST.getlist('order_item')
                quantities = request.POST.getlist('quantity')
                reasons = request.POST.getlist('item_reason')
                
                for item_id, quantity, reason in zip(order_items, quantities, reasons):
                    order_item = OrderItem.objects.get(pk=item_id)
                    quantity_int = int(quantity)
                    
                    returned_qty = PurchaseReturnItem.objects.filter(
                        order_item=order_item
                    ).exclude(return_entry=return_entry).aggregate(
                        Sum('quantity')
                    )['quantity__sum'] or 0
                    
                    max_returnable = order_item.quantity - returned_qty
                    
                    if quantity_int > max_returnable:
                        messages.error(request, 
                            f'الكمية المرتجعة لـ {order_item.product.name} تتجاوز الحد المسموح ({max_returnable})'
                        )
                        return redirect('purchases:return-edit', pk=pk)
                    
                    item_total = quantity_int * order_item.unit_cost
                    subtotal += item_total
                    
                    PurchaseReturnItem.objects.create(
                        return_entry=return_entry,
                        order_item=order_item,
                        quantity=quantity_int,
                        unit_cost=order_item.unit_cost,
                        total_cost=item_total,
                        reason=reason
                    )
                    
                    product = order_item.product
                    product.quantity -= quantity_int  # خصم الكمية الجديدة
                    product.save()
                
                return_entry.total_amount = subtotal
                return_entry.save()
                
                messages.success(request, 'تم تحديث مرتجع الشراء بنجاح!')
                return redirect('purchases:return-detail', pk=return_entry.pk)
    else:
        form = PurchaseReturnForm(instance=return_entry)
    
    return render(request, 'purchases/return_form.html', {
        'form': form,
        'return_entry': return_entry,
        'return_items': return_items,
        'editing': True,
    })

def delete_purchase_return(request, pk):
    return_entry = get_object_or_404(PurchaseReturn, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for item in return_entry.items.all():
                product = item.order_item.product
                product.quantity += item.quantity  # استرجاع الكمية التي تم خصمها
                product.save()
            
            return_entry.delete()
            messages.success(request, 'تم حذف مرتجع الشراء بنجاح!')
            return redirect('purchases:return-list')
    
    return render(request, 'purchases/return_confirm_delete.html', {'return_entry': return_entry})

def get_order_items(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'يجب تحديد أمر الشراء'}, status=400)
    
    try:
        items = OrderItem.objects.filter(order_id=order_id).select_related('product')
        data = []
        
        for item in items:
            returned_qty = PurchaseReturnItem.objects.filter(
                order_item=item
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            max_returnable = item.quantity - returned_qty
            
            if max_returnable > 0:  # عرض فقط الأصناف القابلة للإرجاع
                data.append({
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'original_qty': item.quantity,
                    'unit_cost': float(item.unit_cost),
                    'returned_qty': returned_qty,
                    'max_returnable': max_returnable
                })
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def order_details_json(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    
    items = []
    for item in order.items.all():
        returned_quantity = item.purchasereturnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0
        max_returnable = item.quantity - returned_quantity
        
        items.append({
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_cost': float(item.unit_cost),
            'total_cost': float(item.total_cost),
            'returned_quantity': returned_quantity,
            'max_returnable': max_returnable
        })
    
    data = {
        'order_number': f"PO#{order.id}",
        'order_date': order.order_date.strftime("%Y-%m-%d %H:%M"),
        'supplier_name': order.supplier.name,
        'payment_method': order.payment_method,
        'payment_method_display': order.get_payment_method_display(),
        'total': float(order.total),
        'items': items
    }
    
    return JsonResponse(data)


def get_order_items_for_return(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id parameter is required'}, status=400)
    
    try:
        items = OrderItem.objects.filter(order_id=order_id).select_related('product')
        
        data = [{
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_cost': float(item.unit_cost),
            'total_cost': float(item.total_cost),
            'returned_quantity': item.purchasereturnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'max_returnable': item.quantity - (item.purchasereturnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0)
        } for item in items]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def purchase_order_details_json(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    
    items = []
    for item in order.items.all():
        returned_quantity = item.purchasereturnitem_set.aggregate(Sum('quantity'))['quantity__sum'] or 0
        max_returnable = item.quantity - returned_quantity
        
        items.append({
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_cost': float(item.unit_cost),
            'total_cost': float(item.total_cost),
            'returned_quantity': returned_quantity,
            'max_returnable': max_returnable
        })
    
    data = {
        'order_number': f"PO#{order.id}",
        'order_date': order.order_date.strftime("%Y-%m-%d %H:%M"),
        'supplier_name': order.supplier.name,
        'payment_method': order.payment_method,
        'payment_method_display': order.get_payment_method_display(),
        'total': float(order.total),
        'items': items
    }
    
    return JsonResponse(data)