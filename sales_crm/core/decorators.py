from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def is_sales(user):
    return user.is_authenticated and user.is_sales  # إزالة الأقواس ()

def is_admin(user):
    return user.is_authenticated and user.is_admin  # إزالة الأقواس ()

def sales_required(view_func):
    return user_passes_test(is_sales)(view_func)

def admin_required(view_func):
    return user_passes_test(is_admin)(view_func)

def is_purchases(user):
    return user.is_authenticated and (user.is_purchases or user.is_admin)  # إزالة الأقواس ()

def purchases_required(view_func):
    actual_decorator = user_passes_test(
        is_purchases,
        login_url='core:login',
        redirect_field_name=None
    )
    return actual_decorator(view_func)