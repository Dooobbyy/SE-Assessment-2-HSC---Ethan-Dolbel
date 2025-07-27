# core/forms.py
from django import forms
from .models import Property, Transaction, Scenario, CustomUser
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser, WeeklyRentChange, WeeklyMortgageChange, Tenant
import re
from django.utils import timezone

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'address',
            'purchase_date',
            'tenant_move_in_date',
            'tenant_move_out_date',
            'purchase_price',
            'property_type',
            'weekly_rent',
            'weekly_mortgage',
        ]
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tenant_move_in_date': forms.DateInput(attrs={'type': 'date'}),
            'tenant_move_out_date': forms.DateInput(attrs={'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'weekly_rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'weekly_mortgage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['weekly_rent'].help_text = "Enter weekly rental income (0 if not rented)"
        self.fields['weekly_mortgage'].help_text = "Enter weekly mortgage payment (0 if no mortgage)"
        self.fields['purchase_price'].help_text = "Enter original purchase price"
        # Make purchase_price required
        self.fields['purchase_price'].required = True

class WeeklyRentChangeForm(forms.ModelForm):
    class Meta:
        model = WeeklyRentChange
        fields = ['start_date', 'weekly_rent']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'weekly_rent': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

class WeeklyMortgageChangeForm(forms.ModelForm):
    class Meta:
        model = WeeklyMortgageChange
        fields = ['start_date', 'weekly_mortgage']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'weekly_mortgage': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['move_in_date', 'move_out_date', 'weekly_rent']
        widgets = {
            'move_in_date': forms.DateInput(attrs={'type': 'date'}),
            'move_out_date': forms.DateInput(attrs={'type': 'date'}),
            'weekly_rent': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

class ValuePredictionForm(forms.Form):
    property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    years_ahead = forms.IntegerField(
        min_value=1,
        max_value=30,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Years to Project"
    )
    annual_growth_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=3.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        label="Annual Growth Rate (%)"
    )
    scenario_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Scenario Name (Optional)"
    )

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['property', 'date', 'amount', 'transaction_type', 'description']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BulkTransactionForm(forms.Form):
    properties = forms.ModelMultipleChoiceField(
        queryset=Property.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        required=True
    )
    transaction_type = forms.ChoiceField(
        choices=Transaction.TRANSACTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )

class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        fields = ['name', 'growth_rate', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'growth_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['growth_rate'].help_text = "Enter growth rate as a percentage (e.g., 3.5 for 3.5%)"

class ScenarioComparisonForm(forms.Form):
    property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        required=True,
        label="Select Property"
    )
    years_ahead = forms.IntegerField(
        min_value=1,
        initial=5,
        label="Years to Project",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    scenarios = forms.ModelMultipleChoiceField(
        queryset=Scenario.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Scenarios to Compare"
    )

class SecureUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 4:
            raise forms.ValidationError("Username must be at least 4 characters long.")
        if not re.match("^[a-zA-Z0-9_]+$", username):
            raise forms.ValidationError("Username can only contain letters, numbers, and underscores.")
        return username
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 12:
            raise forms.ValidationError("Password must be at least 12 characters long.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'\d', password):
            raise forms.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("Password must contain at least one special character.")
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class SecureAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    error_messages = {
        'invalid_login': 'Please enter a correct username and password. Note that both fields may be case-sensitive.',
        'inactive': 'This account is inactive.',
    }
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Check if user exists and has too many failed attempts
            try:
                user = CustomUser.objects.get(username=username)
                if user.failed_login_attempts >= 5:
                    from django.core.exceptions import ValidationError
                    raise ValidationError('Account temporarily locked due to too many failed login attempts.')
            except CustomUser.DoesNotExist:
                pass
            
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                # Record failed attempt
                try:
                    user = CustomUser.objects.get(username=username)
                    user.failed_login_attempts += 1
                    user.last_failed_login = timezone.now()
                    user.save()
                except CustomUser.DoesNotExist:
                    pass
                
                raise self.get_invalid_login_error()
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    self.error_messages['inactive'],
                    code='inactive',
                )
            else:
                # Reset failed attempts on successful login
                self.user_cache.reset_failed_attempts()
        return self.cleaned_data