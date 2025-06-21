from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.generic import ListView, DeleteView
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category
from .forms import ProductForm, CategoryForm
from products.models import Product
from django.views.generic import ListView
from products.models import Product
from django.http import JsonResponse
from .models import Product
from django.views.generic import DeleteView, UpdateView
from core.decorators import sales_required

class OutOfStockListView(ListView):
    model = Product
    template_name = 'products/out_of_stock.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(quantity=0).order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'المنتجات النافذة من المخزون'
        return context

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q')
        category = self.request.GET.get('category')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(barcode__icontains=search_query)
            )
        
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset.select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context
        
@sales_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # لاحظ request.FILES هنا
        if form.is_valid():
            product = form.save()
            messages.success(request, 'تم إضافة المنتج بنجاح!')
            return redirect('products:product-list')
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {'form': form})

def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث المنتج بنجاح!')
            return redirect('products:product-list')  # تغيير هنا
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {'form': form})

class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, 'تم حذف المنتج بنجاح!')
        return reverse('products:product-list')

# يمكنك إضافة views مماثلة للفئات (Category) بنفس الطريقة

class CategoryListView(ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الفئة بنجاح!')
            return redirect('products:category-list')
    else:
        form = CategoryForm()
    
    return render(request, 'products/category_form.html', {'form': form})

def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الفئة بنجاح!')
            return redirect('products:category-list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'products/category_form.html', {'form': form})

class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'products/category_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, 'تم حذف الفئة بنجاح!')
        return reverse('products:category-list')
    
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
        'title': f'تفاصيل المنتج: {product.name}'
    }
    return render(request, 'products/product_detail.html', context)    

def get_product_price(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return JsonResponse({'price': float(product.price)})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # الحصول على بنود المبيعات المرتبطة بهذا المنتج
    sale_items = product.get_sale_items()
    
    context = {
        'product': product,
        'sale_items': sale_items,
        'title': f'تفاصيل المنتج: {product.name}'
    }
    return render(request, 'products/product_detail.html', context)

    