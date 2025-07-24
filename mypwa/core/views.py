# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Property, Transaction
from .forms import PropertyForm,  TransactionForm, BulkTransactionForm, ValuePredictionForm
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
from django.db import transaction



TRANSACTION_TYPE_CHOICES = [
    ('rental_income', 'Rental Income'),
    ('additional_income', 'Additional Income'),
    ('other_income', 'Other Income'),
    ('maintenance', 'Maintenance'),
    ('taxes', 'Property Taxes'),
    ('insurance', 'Insurance'),
    ('other_expense', 'Other Expense'),
]



def home(request):
    # Generate last 12 months (including current month)
    today = date.today()
    months = []
    
    # Create list of last 12 months
    for i in range(11, -1, -1):  # 11 down to 0
        month_date = today - relativedelta(months=i)
        months.append({
            'year': month_date.year,
            'month': month_date.month,
            'month_name': calendar.month_abbr[month_date.month],
            'full_date': month_date  # We'll use this for calculations
        })
    
    # Calculate income and expenses for each month
    income_data = []
    expense_data = []
    month_labels = []
    
    for month_info in months:
        year = month_info['year']
        month = month_info['month']
        month_labels.append(f"{month_info['month_name']} {year}")
        
        # Calculate total income for this month
        income = calculate_monthly_income(year, month)
        income_data.append(float(income))
        
        # Calculate total expenses for this month  
        expenses = calculate_monthly_expenses(year, month)
        expense_data.append(float(expenses))
    
    # Calculate summary metrics
    total_income = sum(income_data)
    total_expenses = sum(expense_data)
    net_profit_loss = total_income - total_expenses
    
    context = {
        'months': month_labels,
        'income_data': income_data,
        'expense_data': expense_data,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit_loss': net_profit_loss,
    }
    
    return render(request, 'home.html', context)

def properties(request):
    # Get all properties
    all_properties = Property.objects.all().order_by('-purchase_date')
    
    # Calculate financial data for each property
    properties_with_financials = []
    for property_obj in all_properties:
        # Calculate financials using the functions (not model properties)
        total_income = calculate_property_total_income(property_obj)
        total_expenses = calculate_property_total_expenses(property_obj)
        net_income = total_income - total_expenses
        
        properties_with_financials.append({
            'property': property_obj,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income
        })
    
    context = {
        'properties': properties_with_financials
    }
    
    return render(request, 'properties.html', context)

def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property added successfully!')
            return redirect('properties')
    else:
        form = PropertyForm()
    
    return render(request, 'add_property.html', {'form': form})

def calculate_monthly_income(year, month):
    from django.db import models
    
    total_income = 0
    
    # Get properties owned during this month (purchase date <= end of this month)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    
    # Base rental income from properties
    properties = Property.objects.filter(purchase_date__lte=month_end)
    for property in properties:
        total_income += property.monthly_rent
    
    # Additional income transactions
    additional_income = Transaction.objects.filter(
        date__year=year,
        date__month=month,
        transaction_type__in=['additional_income', 'other_income', 'rental_income']
    ).aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    total_income += additional_income
    return total_income

def calculate_monthly_expenses(year, month):
    from django.db import models
    
    # Get all expense transactions for the month
    expenses = Transaction.objects.filter(
        date__year=year,
        date__month=month,
        transaction_type__in=['maintenance', 'taxes', 'insurance', 'other_expense']
    ).aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    return expenses

def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('properties')
    else:
        form = TransactionForm()
        # Pre-select property if provided in URL
        property_id = request.GET.get('property')
        if property_id:
            form.fields['property'].initial = property_id
    
    return render(request, 'add_transaction.html', {'form': form})

def add_bulk_transaction(request):
    if request.method == 'POST':
        form = BulkTransactionForm(request.POST)
        if form.is_valid():
            properties = form.cleaned_data['properties']
            date_val = form.cleaned_data['date']
            amount = form.cleaned_data['amount']
            transaction_type = form.cleaned_data['transaction_type']
            description = form.cleaned_data['description']
            
            # Create transactions for each selected property
            for property_obj in properties:
                Transaction.objects.create(
                    property=property_obj,
                    date=date_val,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=description
                )
            
            messages.success(request, f'Transaction added to {properties.count()} properties successfully!')
            return redirect('properties')
    else:
        form = BulkTransactionForm()
    
    return render(request, 'add_bulk_transaction.html', {'form': form})

def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Get transactions for this property
    transactions = Transaction.objects.filter(property=property_obj).order_by('-date')
    
    # Calculate financial summary for this property
    total_income = calculate_property_total_income(property_obj)
    total_expenses = calculate_property_total_expenses(property_obj)
    net_income = total_income - total_expenses
    
    context = {
        'property': property_obj,
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
    }
    
    return render(request, 'property_detail.html', context)

def transaction_log(request):
    # Get all transactions, ordered by date (newest first)
    transactions = Transaction.objects.select_related('property').order_by('-date', '-created_at')
    
    # Optional: Add filtering capabilities
    transaction_type = request.GET.get('type')
    property_id = request.GET.get('property')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if property_id:
        transactions = transactions.filter(property_id=property_id)
    
    # Get properties for filter dropdown
    properties = Property.objects.all().order_by('address')
    
    # Calculate summary statistics
    from django.db.models import Sum
    
    # Get filtered transactions for summary (we need to re-filter the base queryset for accurate sums)
    filtered_transactions = Transaction.objects.all()
    if transaction_type:
        filtered_transactions = filtered_transactions.filter(transaction_type=transaction_type)
    if property_id:
        filtered_transactions = filtered_transactions.filter(property_id=property_id)
    
    # Calculate income and expenses
    income_transactions = filtered_transactions.filter(
        transaction_type__in=['rental_income', 'additional_income', 'other_income']
    )
    expense_transactions = filtered_transactions.filter(
        transaction_type__in=['maintenance', 'taxes', 'insurance', 'other_expense']
    )
    
    total_income = income_transactions.aggregate(sum=Sum('amount'))['sum'] or 0
    total_expenses = expense_transactions.aggregate(sum=Sum('amount'))['sum'] or 0
    net_amount = total_income - total_expenses
    
    context = {
        'transactions': transactions,
        'properties': properties,
        'selected_type': transaction_type,
        'selected_property': property_id,
        'transaction_type_choices': TRANSACTION_TYPE_CHOICES,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_amount': net_amount,
        'total_transactions': transactions.count(),
    }
    
    return render(request, 'transaction_log.html', context)

def edit_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            # Handle property deletion
            property_address = property_obj.address
            property_obj.delete()
            messages.success(request, f'Property "{property_address}" has been deleted successfully!')
            return redirect('properties')
        else:
            # Handle property update
            form = PropertyForm(request.POST, instance=property_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Property updated successfully!')
                return redirect('property_detail', property_id=property_obj.id)
            else:
                # Form is not valid, show errors
                messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm(instance=property_obj)
    
    # Calculate financial data directly (instead of using model properties)
    total_income = calculate_property_total_income(property_obj)
    total_expenses = calculate_property_total_expenses(property_obj)
    net_income = total_income - total_expenses
    transaction_count = property_obj.transaction_set.count()
    
    context = {
        'form': form,
        'property': property_obj,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'transaction_count': transaction_count,
    }
    
    return render(request, 'edit_property.html', context)

def calculate_predicted_value(self, years_ahead=5, annual_growth_rate=0.03):
    """Calculate predicted value based on simple growth rate"""
    if not self.purchase_price:
        return 0
    
    from datetime import date
    current_year = date.today().year
    years_owned = current_year - self.purchase_date.year
    total_years = years_owned + years_ahead
    
    # Simple compound growth
    predicted_value = float(self.purchase_price) * ((1 + annual_growth_rate) ** total_years)
    return round(predicted_value, 2)

def tools_home(request):
    """Main tools page"""
    properties = Property.objects.all()
    context = {
        'properties': properties
    }
    return render(request, 'tools/tools_home.html', context)

def property_value_calculator(request):
    """Property value prediction calculator"""
    if request.method == 'POST':
        form = ValuePredictionForm(request.POST)
        if form.is_valid():
            property_obj = form.cleaned_data['property']
            years_ahead = form.cleaned_data['years_ahead']
            growth_rate = form.cleaned_data['annual_growth_rate'] / 100  # Convert percentage to decimal
            scenario_name = form.cleaned_data['scenario_name'] or f"{growth_rate*100}% Growth Scenario"
            
            # Calculate values
            current_value = property_obj.calculate_current_value(growth_rate)
            future_value = property_obj.calculate_future_value(years_ahead, growth_rate)
            roi = property_obj.calculate_roi(growth_rate)
            value_history = property_obj.get_value_history(5, growth_rate)
            
            context = {
                'form': form,
                'property': property_obj,
                'years_ahead': years_ahead,
                'growth_rate': growth_rate * 100,
                'scenario_name': scenario_name,
                'current_value': current_value,
                'future_value': future_value,
                'roi': roi,
                'value_history': value_history,
                'show_results': True
            }
        else:
            context = {'form': form}
    else:
        form = ValuePredictionForm()
        context = {'form': form}
    
    return render(request, 'tools/value_calculator.html', context)

def scenario_modeling(request):
    """Scenario modeling tool"""
    properties = Property.objects.all()
    
    # Default scenarios
    scenarios = [
        {'name': 'Conservative Growth', 'rate': 2.0},
        {'name': 'Moderate Growth', 'rate': 3.5},
        {'name': 'Aggressive Growth', 'rate': 6.0},
        {'name': 'Market Decline', 'rate': -2.0},
    ]
    
    results = []
    
    if request.method == 'POST':
        property_id = request.POST.get('property')
        years_ahead = int(request.POST.get('years_ahead', 5))
        
        if property_id:
            property_obj = get_object_or_404(Property, id=property_id)
            
            for scenario in scenarios:
                growth_rate = scenario['rate'] / 100
                current_value = property_obj.calculate_current_value(growth_rate)
                future_value = property_obj.calculate_future_value(years_ahead, growth_rate)
                roi = property_obj.calculate_roi(growth_rate)
                
                results.append({
                    'property': property_obj,
                    'scenario': scenario,
                    'current_value': current_value,
                    'future_value': future_value,
                    'roi': roi,
                    'years_ahead': years_ahead
                })
    
    context = {
        'properties': properties,
        'scenarios': scenarios,
        'results': results,
        'show_results': len(results) > 0
    }
    
    return render(request, 'tools/scenario_modeling.html', context)

def trend_tracking(request):
    """Trend tracking and comparison tool"""
    properties = Property.objects.filter(purchase_price__isnull=False).exclude(purchase_price=0)
    
    # Calculate portfolio trends
    portfolio_data = []
    total_investment = 0
    total_current_value = 0
    
    for property_obj in properties:
        current_value = property_obj.calculate_current_value(0.03)  # Default 3% growth
        roi = property_obj.calculate_roi(0.03)
        
        portfolio_data.append({
            'property': property_obj,
            'current_value': current_value,
            'roi': roi,
            'purchase_price': float(property_obj.purchase_price)
        })
        
        total_investment += float(property_obj.purchase_price)
        total_current_value += current_value
    
    # Portfolio summary
    portfolio_roi = 0
    if total_investment > 0:
        portfolio_roi = ((total_current_value - total_investment) / total_investment) * 100
    
    context = {
        'properties': properties,
        'portfolio_data': portfolio_data,
        'total_investment': total_investment,
        'total_current_value': total_current_value,
        'portfolio_roi': round(portfolio_roi, 2)
    }
    
    return render(request, 'tools/trend_tracking.html', context)









def calculate_property_total_income(property_obj):
    from django.db import models
    
    total_income = 0
    
    # Debugging: Print property details
    print(f"Calculating income for {property_obj.address}")
    print(f"Monthly Rent: ${property_obj.monthly_rent}")
    
    # Base rental income
    if property_obj.property_type in ['rental', 'owned_outright'] and property_obj.monthly_rent > 0:
        today = date.today()
        purchase_date = property_obj.purchase_date
        months_owned = (today.year - purchase_date.year) * 12 + (today.month - purchase_date.month)
        
        # Debugging: Print months owned
        print(f"Months Owned: {months_owned}")
        
        if months_owned > 0:
            total_income += property_obj.monthly_rent * months_owned
            print(f"Base Rental Income: ${total_income}")
    
    # Additional transactions for this property
    property_income = Transaction.objects.filter(
        property=property_obj,
        transaction_type__in=['rental_income', 'additional_income', 'other_income']
    ).aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    # Debugging: Print additional income
    print(f"Additional Income: ${property_income}")
    
    total_income += property_income
    print(f"Total Income: ${total_income}")
    
    return float(total_income)

def calculate_property_total_expenses(property_obj):
    from django.db import models
    
    total_expenses = 0
    
    # Debugging: Print property details
    print(f"Calculating expenses for {property_obj.address}")
    print(f"Mortgage: ${property_obj.monthly_mortgage}")
    
    # Base mortgage expense
    total_expenses += property_obj.monthly_mortgage
    
    # Additional expense transactions for this property
    property_expenses = Transaction.objects.filter(
        property=property_obj,
        transaction_type__in=['maintenance', 'taxes', 'insurance', 'other_expense']
    ).aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    # Debugging: Print additional expenses
    print(f"Additional Expenses: ${property_expenses}")
    
    total_expenses += property_expenses
    print(f"Total Expenses: ${total_expenses}")
    
    return float(total_expenses)