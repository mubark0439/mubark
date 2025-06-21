from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout  # إضافة هذا الاستيراد

class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated and request.path != reverse('core:login'):
            return redirect(f"{reverse('core:login')}?next={request.path}")
        
        if request.user.is_authenticated:
            # التحقق من أن الحساب نشط أولاً
            if not request.user.is_active_employee():  # استخدم الدالة الموجودة في النموذج
                logout(request)
                messages.error(request, 'حسابك غير نشط (موظف مستقيل أو مفصول)')
                return redirect('core:login')
            
            # التحقق من الصلاحيات حسب المسار
            if request.path.startswith('/admin/') and not request.user.is_staff:
                messages.error(request, 'ليس لديك صلاحية الوصول إلى لوحة الإدارة')
                return redirect('core:dashboard')
            
            if request.path.startswith('/sales/') and not (request.user.is_sales or request.user.is_admin):
                messages.error(request, 'ليس لديك صلاحية الوصول إلى قسم المبيعات')
                return redirect('core:dashboard')
            
            if request.path.startswith('/purchases/') and not (request.user.is_purchases or request.user.is_admin):
                messages.error(request, 'ليس لديك صلاحية الوصول إلى قسم المشتريات')
                return redirect('core:dashboard')
            
            if request.path.startswith('/employees/') and not request.user.is_admin:
                messages.error(request, 'ليس لديك صلاحية الوصول إلى إدارة الموظفين')
                return redirect('core:dashboard')
            
            if request.path.startswith('/purchases/') and request.user.is_sales:
                messages.error(request, 'ليس لديك صلاحية الوصول إلى قسم المشتريات')
                return redirect('core:dashboard')

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
    
class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active_account():
            logout(request)
            return redirect('core:login')
            
        return self.get_response(request)    