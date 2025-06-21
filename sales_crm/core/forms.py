from django import forms
from .models import Customer, User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'العنوان التفصيلي'
            }),
        }

class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_active_account():
            raise forms.ValidationError(
                'هذا الحساب غير نشط (موظف مستقيل أو مفصول)',
                code='inactive_account'
            )

class EmployeeCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone', 'status', 
                 'basic_salary', 'housing_allowance', 'transportation_allowance',
                 'joining_date', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "اسم المستخدم"
        self.fields['email'].label = "البريد الإلكتروني"
        self.fields['role'].label = "الدور"
        self.fields['phone'].label = "الهاتف"
        self.fields['status'].label = "حالة الموظف"
        self.fields['basic_salary'].label = "الراتب الأساسي"
        self.fields['housing_allowance'].label = "بدل السكن"
        self.fields['transportation_allowance'].label = "بدل النقل"
        self.fields['joining_date'].label = "تاريخ التعيين"
        
        for field_name, field in self.fields.items():
            if field_name in ['role', 'status']:
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'phone', 'status',
                 'basic_salary', 'housing_allowance', 'transportation_allowance',
                 'joining_date', 'termination_date']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field in ['role', 'status']:
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        termination_date = cleaned_data.get('termination_date')
        
        if status in ['resigned', 'terminated']:
            if not termination_date:
                cleaned_data['termination_date'] = timezone.now().date()
        else:
            cleaned_data['termination_date'] = None
        
        return cleaned_data