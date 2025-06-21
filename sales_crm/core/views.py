from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic.edit import DeleteView
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Customer, User
from .forms import CustomerForm, LoginForm, EmployeeCreationForm, UserUpdateForm
from django.utils import timezone
from django.db.models import Sum, F
from sales.models import Sale, SaleItem, Return
from products.models import Product
from django.views.generic import CreateView, UpdateView
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.csrf import csrf_protect

# دالة مساعدة للتحقق من الصلاحيات
def is_admin(user):
    return user.is_authenticated and user.is_admin()

@login_required
def dashboard(request):
    # إحصائيات العملاء
    total_customers = Customer.objects.count()
    recent_customers = Customer.objects.order_by('-created_at')[:5]

    # إحصائيات المنتجات
    total_products = Product.objects.count()
    out_of_stock_products = Product.objects.filter(quantity=0).count()
    out_of_stock_items = Product.objects.filter(quantity=0).order_by('-updated_at')[:5]

    # حساب التواريخ
    today = timezone.now().date()
    month_start = today.replace(day=1)
    current_month = today.month
    current_year = today.year
    
    # حساب المبيعات اليومية (الصافية بعد خصم المرتجعات)
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    daily_sales_total = Sale.objects.filter(
        sale_date__gte=today_start,
        sale_date__lt=today_end
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    daily_returns_total = Return.objects.filter(
        return_date__gte=today_start,
        return_date__lt=today_end,
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    daily_sales = {
        'net': daily_sales_total - daily_returns_total,
        'returns': daily_returns_total,
        'gross': daily_sales_total
    }
    
    # حساب المبيعات الشهرية (الصافية بعد خصم المرتجعات)
    monthly_sales_total = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    monthly_returns_total = Return.objects.filter(
        return_date__year=current_year,
        return_date__month=current_month,
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    monthly_sales = {
        'net': monthly_sales_total - monthly_returns_total,
        'returns': monthly_returns_total,
        'gross': monthly_sales_total
    }
    
    # حساب الربح الشهري (الصافي بعد خصم المرتجعات)
    monthly_profit_items = SaleItem.objects.filter(
        sale__sale_date__year=current_year,
        sale__sale_date__month=current_month
    ).annotate(
        profit=(F('unit_price') - F('product__cost')) * F('quantity')
    ).aggregate(total_profit=Sum('profit'))['total_profit'] or 0

    monthly_returns_profit = Return.objects.filter(
        return_date__year=current_year,
        return_date__month=current_month,
        status='completed'
    ).annotate(
        loss=Sum(F('items__unit_price') * F('items__quantity'))
    ).aggregate(total_loss=Sum('loss'))['total_loss'] or 0

    monthly_profit = {
        'net': monthly_profit_items - monthly_returns_profit,
        'returns': monthly_returns_profit,
        'gross': monthly_profit_items
    }

    # المرتجعات الحديثة
    recent_returns = Return.objects.order_by('-return_date')[:5]

    context = {
        'title': 'لوحة التحكم',
        'total_customers': total_customers,
        'total_products': total_products,
        'out_of_stock_products': out_of_stock_products,
        'recent_customers': recent_customers,
        'out_of_stock_items': out_of_stock_items,
        'daily_sales': daily_sales,
        'monthly_sales': monthly_sales,
        'monthly_profit': monthly_profit,
        'today': today,
        'current_month': current_month,
        'current_year': current_year,
        'recent_returns': recent_returns
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def customer_list(request):
    # البحث
    search_query = request.GET.get('q', '')
    customers_list = Customer.objects.all()
    
    if search_query:
        customers_list = customers_list.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # الترقيم الصفحي
    paginator = Paginator(customers_list, 10)  # 10 عملاء لكل صفحة
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'core/customers/list.html', context)

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, 'تم إنشاء العميل بنجاح!')
            return redirect('core:customer-detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'إضافة عميل جديد'
    }
    return render(request, 'core/customers/form.html', context)

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = {
        'customer': customer,
        'title': f'تفاصيل العميل: {customer.name}'
    }
    return render(request, 'core/customers/detail.html', context)

@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات العميل بنجاح!')
            return redirect('core:customer-detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'title': f'تعديل العميل: {customer.name}',
        'customer': customer
    }
    return render(request, 'core/customers/form.html', context)

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'core/customers/confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, 'تم حذف العميل بنجاح!')
        return reverse('core:customer-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'حذف العميل: {self.object.name}'
        return context

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'core/customers/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة عميل جديد'
        return context
    
    def form_valid(self, form):
        customer = form.save()
        messages.success(self.request, 'تم إنشاء العميل بنجاح!')
        return redirect('core:customer-detail', pk=customer.pk)

# دوال تسجيل الدخول والخروج
def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # التحقق من حالة الموظف
            if user.status in ['resigned', 'terminated']:
                messages.error(request, 'حسابك غير نشط (موظف مستقيل أو مفصول)')
                return redirect('core:login')
                
            login(request, user)
            messages.success(request, 'تم تسجيل الدخول بنجاح!')
            return redirect('core:dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'core/auth/login.html', {'form': form})

def user_logout(request):
    # مسح كافة بيانات الجلسة
    request.session.flush()
    
    # تسجيل الخروج
    logout(request)
    
    # حذف كافة الكوكيز
    response = redirect('core:login')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    
    # إضافة رؤوس لمنع التخزين المؤقت
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    messages.success(request, 'تم تسجيل الخروج بنجاح!')
    return response

# دوال إدارة الموظفين
@login_required
@user_passes_test(is_admin)
def employee_list(request):
    employees = User.objects.all()
    return render(request, 'core/employees/list.html', {'employees': employees})

class EmployeeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = EmployeeCreationForm
    template_name = 'core/employees/form.html'
    success_url = reverse_lazy('core:employee-list')
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def form_valid(self, form):
        messages.success(self.request, 'تم إنشاء الموظف بنجاح!')
        return super().form_valid(form)

class EmployeeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'core/employees/form.html'
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_current_user'] = self.object == self.request.user
        context['total_salary'] = self.object.total_salary
        return context
    
    def form_valid(self, form):
        if form.instance == self.request.user and 'role' in form.changed_data:
            form.add_error('role', 'لا يمكن تغيير دور المدير الحالي')
            return self.form_invalid(form)
        
        status = form.cleaned_data.get('status')
        if status in ['resigned', 'terminated']:
            if not form.cleaned_data.get('termination_date'):
                form.instance.termination_date = timezone.now().date()
        else:
            form.instance.termination_date = None
        
        messages.success(self.request, 'تم تحديث بيانات الموظف بنجاح!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('core:employee-list')

class EmployeeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'core/employees/confirm_delete.html'
    success_url = reverse_lazy('core:employee-list')
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف الموظف بنجاح!')
        return super().delete(request, *args, **kwargs)