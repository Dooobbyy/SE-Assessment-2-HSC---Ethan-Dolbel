from django.shortcuts import render, redirect
from .models import Property, Income, Expense
from datetime import datetime, date
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
import calendar
from .forms import PropertyForm, IncomeFormSet, ExpenseFormSet
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

def index(request):
    properties = Property.objects.all()
    incomes = Income.objects.all()
    expenses = Expense.objects.all()

    total_portfolio_value = sum(p.current_value or p.purchase_price for p in properties)
    total_income = sum(i.amount for i in incomes)
    total_expenses = sum(e.amount for e in expenses)
    monthly_cash_flow = total_income - total_expenses

    now = datetime.now()
    current_month = now.strftime('%B')

    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    
    context = {
        'total_portfolio_value': total_portfolio_value,
        'monthly_cash_flow': monthly_cash_flow,
        'properties': properties,
        'incomes': incomes,
        'expenses': expenses,
        'total_portfolio_value': 1000000,
        'monthly_cash_flow': 2000,
        'properties': Property.objects.all(),
        'months': months,
        'current_month': current_month,
    }
    return render(request, 'index.html', context)

def get_monthly_summary(month, year):
    # Get all income for the given month/year
    income_list = Income.objects.filter(date__month=month, date__year=year)
    total_income = sum(income.amount for income in income_list)

    # Get all expenses for the given month/year
    expense_list = Expense.objects.filter(date__month=month, date__year=year)
    total_expenses = sum(expense.amount for expense in expense_list)

    net_profit = round(total_income - total_expenses, 2)

    return {
        'netProfit': f"+ ${total_income - total_expenses:.2f}",
        'maintenanceCosts': f"– ${sum(e.amount for e in expense_list if e.category == 'Maintenance'):.2f}",
        'finalCashFlow': f"= ${net_profit:.2f}"
    }

def index(request):
    # Default values when no month is selected
    now = datetime.now()
    current_month = now.strftime('%B')

    # Get all properties
    properties = Property.objects.all()

    # Generate monthly summary based on current month
    summary = get_monthly_summary(now.month, now.year)

    context = {
        'months': ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December'],
        'summary_data': summary,
        'properties': properties,
        'current_month': current_month,
    }

    return render(request, 'index.html', context)

def get_monthly_summary_ajax(request):
    month_name = request.GET.get('month', datetime.now().strftime('%B'))
    year = request.GET.get('year', datetime.now().year)

    # Map month name to number (e.g., 'January' → 1)
    month_number = list(calendar.month_name).index(month_name)

    # Get income/expense for selected month/year
    income_list = Income.objects.filter(date__month=month_number, date__year=year)
    expense_list = Expense.objects.filter(date__month=month_number, date__year=year)

    total_income = sum(i.amount for i in income_list)
    total_expenses = sum(e.amount for e in expense_list)
    maintenance_costs = sum(e.amount for e in expense_list if e.category == 'Maintenance')

    net_profit = round(total_income - total_expenses, 2)

    data = {
        'netProfit': f"+ ${total_income - total_expenses:.2f}",
        'maintenanceCosts': f"– ${maintenance_costs:.2f}",
        'finalCashFlow': f"= ${net_profit:.2f}"
    }

    return JsonResponse(data)

def get_chart_data(request):
    # Get selected month/year (defaults to current)
    month_name = request.GET.get('month', datetime.now().strftime('%B'))
    year = int(request.GET.get('year', datetime.now().year))
    
    try:
        month_number = list(calendar.month_name).index(month_name)
    except ValueError:
        month_number = datetime.now().month

    # Find the earliest purchase date across all properties
    earliest_purchase = Property.objects.order_by('purchase_date').first()
    if earliest_purchase:
        start_year = earliest_purchase.purchase_date.year
        start_month = earliest_purchase.purchase_date.month
    else:
        start_year = datetime.now().year
        start_month = 1

    current_year = datetime.now().year
    current_month = datetime.now().month

    monthly_labels = []
    monthly_income_data = []
    monthly_expense_data = []

    # Generate data for every month from earliest purchase to current month/year
    for year_iter in range(start_year, current_year + 1):
        for month_iter in range(1, 13):
            # Skip months after current month in current year
            if year_iter == current_year and month_iter > current_month:
                continue

            # Skip months before earliest purchase date in start_year
            if year_iter == start_year and month_iter < start_month:
                continue

            # Calculate totals for this month/year
            income_total = sum(
                i.amount for i in Income.objects.filter(
                    date__year=year_iter,
                    date__month=month_iter
                )
            )

            expense_total = sum(
                e.amount for e in Expense.objects.filter(
                    date__year=year_iter,
                    date__month=month_iter
                )
            )

            # Add to datasets
            monthly_labels.append(f"{calendar.month_abbr[month_iter - 1]} {year_iter}")
            monthly_income_data.append(income_total)
            monthly_expense_data.append(expense_total)

    return JsonResponse({
        'monthlyLabels': monthly_labels,
        'monthlyIncomeData': monthly_income_data,
        'monthlyExpenseData': monthly_expense_data,
    })




def get_pie_chart_data(request):
    month_name = request.GET.get('month', datetime.now().strftime('%B'))

    try:
        month_number = list(calendar.month_name).index(month_name)
    except ValueError:
        month_number = datetime.now().month

    year = int(request.GET.get('year', datetime.now().year))

    properties = Property.objects.all()
    combined = []

    for prop in properties:
        income_total = sum(i.amount for i in Income.objects.filter(property=prop, date__month=month_number, date__year=year))
        expense_total = sum(e.amount for e in Expense.objects.filter(property=prop, date__month=month_number, date__year=year))
        profit = round(float(income_total - expense_total), 2)
        combined.append((prop.name, profit))

    # Sort descending by profit
    combined.sort(key=lambda x: x[1], reverse=True)

    labels = []
    values = []

    if len(combined) >= 1:
        labels.append(combined[0][0])
        values.append(combined[0][1])

    if len(combined) >= 2:
        labels.append(combined[1][0])
        values.append(combined[1][1])

    if len(combined) >= 3:
        labels.append(combined[2][0])
        values.append(combined[2][1])

    if len(combined) > 3:
        rest_sum = sum(val for name, val in combined[3:])
        labels.append("Other Properties")
        values.append(round(rest_sum, 2))

    return JsonResponse({
        'propertyLabels': labels or ['No Properties'],
        'propertyValues': values or [0]
    })


def properties_view(request):
    properties = Property.objects.all()
    property_list = []

    for prop in properties:
        # Get latest rent income (only if exists)
        rent = sum(
            i.amount for i in Income.objects.filter(
                property=prop,
                description="Rental Income"
            )
        ) or 0  # Default to 0 if no income

        # Get latest mortgage expense (only if exists)
        mortgage = sum(
            e.amount for e in Expense.objects.filter(
                property=prop,
                category="Mortgage"
            )
        ) or 0  # Default to 0 if no expense

        property_list.append({
            'name': prop.name,
            'address': prop.address,
            'purchase_price': prop.purchase_price,
            'rent': rent,
            'mortgage': mortgage
        })
    return render(request, 'properties.html', {'properties': property_list})

def add_property(request):
    if request.method == 'POST':
        property_form = PropertyForm(request.POST)
        rent = float(request.POST.get('rent', 0))
        mortgage = float(request.POST.get('mortgage', 0))

        if property_form.is_valid():
            property = property_form.save()

            # Get purchase date
            purchase_date = property.purchase_date
            start_date = purchase_date.replace(day=1)  # Use 1st of the month
            end_date = date.today().replace(day=1)

            current_date = start_date

            # Generate monthly Income (Rent)
            while current_date <= end_date:
                Income.objects.create(
                    property=property,
                    amount=rent,
                    description='Rental Income',
                    date=current_date
                )

                # Move to next month
                current_date += relativedelta(months=1)

            current_date = start_date

            # Generate monthly Expense (Mortgage)
            while current_date <= end_date:
                Expense.objects.create(
                    property=property,
                    amount=mortgage,
                    category='Mortgage',
                    date=current_date
                )

                current_date += relativedelta(months=1)

            return redirect('properties')

    else:
        property_form = PropertyForm()

    return render(request, 'add_property.html', {
        'property_form': property_form
    })