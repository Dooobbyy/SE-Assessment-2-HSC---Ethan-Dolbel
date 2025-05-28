from django.shortcuts import render
from .models import Property, Income, Expense
from datetime import datetime
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
import calendar

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
    month_name = request.GET.get('month', datetime.now().strftime('%B'))
    
    # Convert month name to number (e.g., 'May' → 5)
    try:
        month_number = list(calendar.month_name).index(month_name)
    except ValueError:
        month_number = datetime.now().month

    year = int(request.GET.get('year', datetime.now().year))

    monthly_labels = []
    monthly_income_data = []
    monthly_expense_data = []

    # Generate last 6 months including selected month
    for i in range(5, -1, -1):
        m = month_number - i
        y = year
        if m < 1:
            m += 12
            y -= 1
        m = m % 12 or 12  # Wrap around to December

        income_total = sum(i.amount for i in Income.objects.filter(date__month=m, date__year=y))
        expense_total = sum(e.amount for e in Expense.objects.filter(date__month=m, date__year=y))

        monthly_labels.append(calendar.month_abbr[m])
        monthly_income_data.append(income_total)
        monthly_expense_data.append(expense_total)

    return JsonResponse({
        'monthlyLabels': monthly_labels,
        'monthlyIncomeData': monthly_income_data,
        'monthlyExpenseData': monthly_expense_data,
    })