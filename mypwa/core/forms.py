# core/forms.py
from django import forms
from .models import Property, Transaction, Scenario

from django import forms
from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['address', 'purchase_date', 'purchase_price', 'property_type', 'monthly_rent', 'monthly_mortgage']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'monthly_mortgage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['monthly_rent'].help_text = "Enter monthly rental income (0 if not rented)"
        self.fields['monthly_mortgage'].help_text = "Enter monthly mortgage payment (0 if no mortgage)"
        self.fields['purchase_price'].help_text = "Enter original purchase price"
        # Make purchase_price required
        self.fields['purchase_price'].required = True

# Add a form for value prediction scenarios
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