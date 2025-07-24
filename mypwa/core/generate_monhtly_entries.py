# management/commands/generate_monthly_entries.py
from django.core.management.base import BaseCommand
from datetime import date
from dateutil.relativedelta import relativedelta
from models import Property, Income, Expense

class Command(BaseCommand):
    help = 'Generates monthly income and expense entries for properties'

    def handle(self, *args, **kwargs):
        today = date.today().replace(day=1)
        properties = Property.objects.all()

        for prop in properties:
            last_income = Income.objects.filter(property=prop).order_by('-date').first()
            last_expense = Expense.objects.filter(property=prop).order_by('-date').first()

            next_income_date = (last_income.date.replace(day=1) + relativedelta(months=1)) if last_income else prop.purchase_date.replace(day=1)
            next_expense_date = (last_expense.date.replace(day=1) + relativedelta(months=1)) if last_expense else prop.purchase_date.replace(day=1)

            # Generate Income
            while next_income_date <= today:
                Income.objects.get_or_create(
                    property=prop,
                    date=next_income_date,
                    defaults={'amount': prop.monthly_rent, 'description': 'Rental Income'}
                )
                next_income_date += relativedelta(months=1)

            # Generate Expense
            while next_expense_date <= today:
                Expense.objects.get_or_create(
                    property=prop,
                    date=next_expense_date,
                    defaults={'amount': prop.monthly_mortgage, 'category': 'Mortgage'}
                )
                next_expense_date += relativedelta(months=1)

        self.stdout.write(self.style.SUCCESS('Monthly entries generated successfully'))