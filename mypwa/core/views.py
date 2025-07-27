# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import HttpResponse
from .models import Property, Transaction, Scenario
from .forms import PropertyForm, TransactionForm, BulkTransactionForm, ValuePredictionForm, ScenarioComparisonForm, ScenarioForm, SecureUserCreationForm, SecureAuthenticationForm, WeeklyRentChangeForm, WeeklyMortgageChangeForm, TenantForm
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import logging


TRANSACTION_TYPE_CHOICES = [
    ('rental_income', 'Rental Income'),
    ('additional_income', 'Additional Income'),
    ('other_income', 'Other Income'),
    ('maintenance', 'Maintenance'),
    ('taxes', 'Property Taxes'),
    ('insurance', 'Insurance'),
    ('other_expense', 'Other Expense'),
]

logger = logging.getLogger(__name__)


@csrf_protect
@never_cache
def register(request):
    if request.method == 'POST':
        form = SecureUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = SecureUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@csrf_protect
@never_cache
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Change this line from 'index' to 'dashboard'
                return redirect('dashboard')  # This matches your URL name
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

class LoginView(View):
    template_name = 'registration/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')  # Change to your dashboard URL
        form = SecureAuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = SecureAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log successful login
            logger.info(f"Successful login for user: {user.username} from IP: {get_client_ip(request)}")
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', '/dashboard/')  # Change to your dashboard URL
            return redirect(next_page)
        else:
            # Log failed login attempt
            username = request.POST.get('username')
            logger.warning(f"Failed login attempt for user: {username} from IP: {get_client_ip(request)}")
            
        return render(request, self.template_name, {'form': form})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@method_decorator([csrf_protect, never_cache], name='dispatch')
class RegisterView(View):
    template_name = 'registration/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = SecureUserCreationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = SecureUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            logger.info(f"New user registered: {user.username}")
            return redirect('login')
        return render(request, self.template_name, {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def home(request):
    print(f"User is authenticated: {request.user.is_authenticated}")  # Debug statement
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

        # Correct way to call the functions:
        income = calculate_monthly_income(year, month)  # Pass only year and month
        income_data.append(float(income))

        expenses = calculate_monthly_expenses(year, month) # Pass only year and month
        expense_data.append(float(expenses))
    
    # Calculate summary metrics
    total_income = sum(property_obj.calculate_total_income() for property_obj in Property.objects.all())
    total_expenses = sum(property_obj.calculate_total_expenses() for property_obj in Property.objects.all())
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

@login_required
def properties(request):
    # Get all properties
    all_properties = Property.objects.all().order_by('-purchase_date')
    
    # Prepare data for the template
    properties_with_financials = []
    for property_obj in all_properties:
        prop_data = {
            'property': property_obj,
            'total_income': property_obj.calculate_total_income(),
            'total_expenses': property_obj.calculate_total_expenses(),
            'net_income': property_obj.calculate_net_income(),
        }
        properties_with_financials.append(prop_data)
    
    context = {
        'properties': properties_with_financials
    }
    
    return render(request, 'properties.html', context)

@login_required
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

def add_tenant(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.property = property_obj
            tenant.save()
            return redirect('property_detail', property_id=property_id)
    else:
        form = TenantForm()
    
    return render(request, 'add_tenant.html', {'form': form})

def calculate_monthly_income(year, month):
    from django.db.models import Sum
    from datetime import date, timedelta
    import calendar
    from decimal import Decimal
    
    total_income = Decimal('0.00')
    
    # Get all properties
    properties = Property.objects.all()
    
    # Add base rental income for properties that were owned during this month
    for property_obj in properties:
        # Check if property was owned during this month
        if property_obj.purchase_date.year < year or (property_obj.purchase_date.year == year and property_obj.purchase_date.month <= month):
            # For rental and owned_outright properties, add weekly rent converted to monthly
            if property_obj.property_type in ['rental', 'owned_outright'] and property_obj.weekly_rent > 0:
                # Calculate accurate monthly rent based on days in the month
                days_in_month = calendar.monthrange(year, month)[1]
                start_date = date(year, month, 1)
                end_date = date(year, month, days_in_month)
                
                # Exclude the purchase week
                first_payday = property_obj.purchase_date + timedelta(days=(4 - property_obj.purchase_date.weekday()))
                if first_payday <= end_date:
                    start_date = max(first_payday, property_obj.tenant_move_in_date or start_date)
                    end_date = min(end_date, property_obj.tenant_move_out_date or end_date)
                    
                    # Count Fridays in the month
                    current_date = start_date
                    while current_date <= end_date:
                        if current_date.weekday() == 4:  # Friday
                            total_income += Decimal(str(property_obj.weekly_rent))
                        
                        current_date += timedelta(days=1)
    
    # Add transaction-based income for this specific month
    month_income_result = Transaction.objects.filter(
        date__year=year,
        date__month=month,
        transaction_type__in=['rental_income', 'additional_income', 'other_income']
    ).aggregate(Sum('amount'))['amount__sum']
    
    month_income = month_income_result or Decimal('0.00')
    
    total_income += month_income
    return float(total_income)

def calculate_monthly_expenses(year, month):
    from django.db.models import Sum
    from datetime import date
    import calendar
    from decimal import Decimal
    
    total_expenses = Decimal('0.00')
    
    # Get all properties
    properties = Property.objects.all()
    
    # Add base mortgage expenses for properties that were owned during this month
    # EXCEPT for owned_outright properties (they don't have mortgages)
    for property_obj in properties:
        # Check if property was owned during this month
        if property_obj.purchase_date.year < year or (property_obj.purchase_date.year == year and property_obj.purchase_date.month <= month):
            # Add weekly mortgage converted to monthly for properties that are NOT owned_outright
            if property_obj.property_type != 'owned_outright' and property_obj.weekly_mortgage > 0:
                # Calculate accurate monthly mortgage based on days in the month
                days_in_month = calendar.monthrange(year, month)[1]
                weekly_mortgage_decimal = Decimal(str(property_obj.weekly_mortgage))
                days_in_month_decimal = Decimal(str(days_in_month))
                monthly_mortgage = weekly_mortgage_decimal * (days_in_month_decimal / Decimal('7'))
                total_expenses += monthly_mortgage
    
    # Add transaction-based expenses for this specific month
    month_expenses_result = Transaction.objects.filter(
        date__year=year,
        date__month=month,
        transaction_type__in=['maintenance', 'taxes', 'insurance', 'other_expense']
    ).aggregate(Sum('amount'))['amount__sum']
    
    month_expenses = month_expenses_result or Decimal('0.00')
    
    total_expenses += month_expenses
    return float(total_expenses)

def add_weekly_rent_change(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        form = WeeklyRentChangeForm(request.POST)
        if form.is_valid():
            change = form.save(commit=False)
            change.property = property_obj
            change.save()
            return redirect('property_detail', property_id=property_id)
    else:
        form = WeeklyRentChangeForm()
    
    return render(request, 'add_weekly_rent_change.html', {'form': form})

def add_weekly_mortgage_change(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        form = WeeklyMortgageChangeForm(request.POST)
        if form.is_valid():
            change = form.save(commit=False)
            change.property = property_obj
            change.save()
            return redirect('property_detail', property_id=property_id)
    else:
        form = WeeklyMortgageChangeForm()
    
    return render(request, 'add_weekly_mortgage_change.html', {'form': form})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('properties')  # Changed from 'transaction_log' to 'properties'
    else:
        form = TransactionForm()
        # Pre-select property if provided in URL
        property_id = request.GET.get('property')
        if property_id:
            form.fields['property'].initial = property_id
    
    return render(request, 'add_transaction.html', {'form': form})

@login_required
def add_bulk_transaction(request):
    if request.method == 'POST':
        form = BulkTransactionForm(request.POST)
        if form.is_valid():
            properties = form.cleaned_data['properties']  # This is a QuerySet
            date_val = form.cleaned_data['date']
            amount = form.cleaned_data['amount']
            transaction_type = form.cleaned_data['transaction_type']
            description = form.cleaned_data['description']
            
            # Create transactions for each selected property
            created_count = 0
            for property_obj in properties:
                Transaction.objects.create(
                    property=property_obj,
                    date=date_val,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=description
                )
                created_count += 1
            
            messages.success(request, f'Transaction added to {created_count} properties successfully!')
            return redirect('transaction_log')  # Redirect to transaction log instead of properties
    else:
        form = BulkTransactionForm()
    
    # Pass the properties queryset to the template for better control if needed
    properties_for_template = Property.objects.all().order_by('address')
    
    return render(request, 'add_bulk_transaction.html', {
        'form': form,
        'properties': properties_for_template
    })

@login_required
def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Get transactions for this property
    transactions = Transaction.objects.filter(property=property_obj).order_by('-date')
    
    # Calculate financial summary for this property USING THE MODEL METHODS
    total_income = property_obj.calculate_total_income()  # Call method on the instance
    total_expenses = property_obj.calculate_total_expenses()  # Call method on the instance
    net_income = property_obj.calculate_net_income()  # Call method on the instance
    
    context = {
        'property': property_obj,
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
    }
    
    return render(request, 'property_detail.html', context)

@login_required
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

@login_required
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
                messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyForm(instance=property_obj)
    
    # Calculate financial data using model methods
    total_income = property_obj.calculate_total_income()
    total_expenses = property_obj.calculate_total_expenses()
    net_income = property_obj.calculate_net_income()
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

@login_required
def tools_home(request):
    """Main tools page"""
    properties = Property.objects.all()
    context = {
        'properties': properties
    }
    return render(request, 'tools/tools_home.html', context)

@login_required
def property_value_calculator(request):
    """Property value prediction calculator"""
    if request.method == 'POST':
        # Check if user wants to clear the projection
        if 'clear_projection' in request.POST:
            # Clear the session or redirect to clean state
            return redirect('value_calculator')
        
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

@login_required
def add_scenario(request):
    if request.method == 'POST':
        form = ScenarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scenario added successfully!')
            return redirect('scenario_list')
    else:
        form = ScenarioForm()
    
    return render(request, 'tools/add_scenario.html', {'form': form})

@login_required
def scenario_list(request):
    scenarios = Scenario.objects.all().order_by('-created_at')
    return render(request, 'tools/scenario_list.html', {'scenarios': scenarios})

@login_required
def delete_scenario(request, scenario_id):
    scenario = get_object_or_404(Scenario, id=scenario_id)
    if request.method == 'POST':
        scenario_name = scenario.name
        scenario.delete()
        messages.success(request, f'Scenario "{scenario_name}" deleted successfully!')
        return redirect('scenario_list')
    return render(request, 'tools/delete_scenario.html', {'scenario': scenario})

@login_required
def scenario_comparison(request):
    if request.method == 'POST':
        form = ScenarioComparisonForm(request.POST)
        if form.is_valid():
            property_obj = form.cleaned_data['property']
            years_ahead = form.cleaned_data['years_ahead']
            selected_scenarios = form.cleaned_data['scenarios']
            
            # Calculate values for each scenario
            results = []
            for scenario in selected_scenarios:
                growth_rate = float(scenario.growth_rate) / 100
                current_value = property_obj.calculate_current_value(growth_rate)
                future_value = property_obj.calculate_future_value(years_ahead, growth_rate)
                roi = property_obj.calculate_roi(growth_rate)
                
                results.append({
                    'scenario': scenario,
                    'current_value': current_value,
                    'future_value': future_value,
                    'roi': roi,
                })
            
            context = {
                'form': form,
                'results': results,
                'property': property_obj,
                'years_ahead': years_ahead,
                'show_results': True
            }
        else:
            context = {'form': form}
    else:
        form = ScenarioComparisonForm()
        context = {'form': form}
    
    return render(request, 'tools/scenario_comparison.html', context)

@login_required
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
        purchase_price = float(property_obj.purchase_price)
        
        # Calculate value change (this is what was causing issues in the template)
        value_change = current_value - purchase_price
        
        portfolio_data.append({
            'property': property_obj,
            'current_value': current_value,
            'roi': roi,
            'purchase_price': purchase_price,
            'value_change': value_change  # Add this calculated value
        })
        
        total_investment += purchase_price
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

@login_required
def edit_transaction(request, transaction_id):
    transaction_obj = get_object_or_404(Transaction, id=transaction_id)
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            # Handle transaction deletion
            transaction_description = transaction_obj.description or f"{transaction_obj.get_transaction_type_display()} transaction"
            property_address = transaction_obj.property.address if transaction_obj.property else "No Property"
            transaction_obj.delete()
            messages.success(request, f'Transaction "{transaction_description}" for {property_address} has been deleted successfully!')
            return redirect('transaction_log')
        else:
            # Handle transaction update
            form = TransactionForm(request.POST, instance=transaction_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Transaction updated successfully!')
                return redirect('transaction_log')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = TransactionForm(instance=transaction_obj)
    
    context = {
        'form': form,
        'transaction': transaction_obj,
    }
    
    return render(request, 'edit_transaction.html', context)