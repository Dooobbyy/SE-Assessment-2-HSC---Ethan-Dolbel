from django import forms
from django.forms import inlineformset_factory
from .models import Property, Income, Expense

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'purchase_date', 'purchase_price', 'current_value']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'})
        }

# IncomeFormSet → includes amount and date
IncomeFormSet = inlineformset_factory(
    Property,
    Income,
    fields=('amount', 'date', 'description'),
    extra=0,  # ← No extra fields
    can_delete=False
)

# ExpenseFormSet → includes amount and date
ExpenseFormSet = inlineformset_factory(
    Property,
    Expense,
    fields=('amount', 'date', 'category'),
    extra=0,
    can_delete=False
)