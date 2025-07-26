from django.db import models
from django.utils import timezone
from datetime import date
import calendar


class Property(models.Model):
    PROPERTY_TYPES = [
        ('rental', 'Rental Property'),
        ('owner_occupied', 'Owner Occupied'),
        ('owned_outright', 'Owned Outright'),
    ]
    
    address = models.CharField(max_length=200)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False, help_text="Original purchase price")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='rental')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_mortgage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.address} ({self.get_property_type_display()})"
    
    @property
    def is_rental(self):
        return self.property_type == 'rental'
    
    @property
    def is_owner_occupied(self):
        return self.property_type == 'owner_occupied'
    
    @property
    def is_owned_outright(self):
        return self.property_type == 'owned_outright'
    
    # Calculate total income for the property
    def calculate_total_income(self):
        from django.db.models import Sum
        
        total_income = 0
        
        # Debugging: Print property details
        print(f"Calculating income for {self.address}")
        print(f"Monthly Rent: ${self.monthly_rent}")
        
        # Base rental income
        if self.property_type in ['rental', 'owned_outright'] and self.monthly_rent > 0:
            today = date.today()
            purchase_date = self.purchase_date
            months_owned = (today.year - purchase_date.year) * 12 + (today.month - purchase_date.month)
            
            # Debugging: Print months owned
            print(f"Months Owned: {months_owned}")
            
            if months_owned > 0:
                total_income += self.monthly_rent * months_owned
                print(f"Base Rental Income: ${total_income}")
        
        # Additional transactions for this property
        property_income = Transaction.objects.filter(
            property=self,
            transaction_type__in=['rental_income', 'additional_income', 'other_income']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Debugging: Print additional income
        print(f"Additional Income: ${property_income}")
        
        total_income += property_income
        print(f"Total Income: ${total_income}")
        
        return float(total_income)
    
    # Calculate total expenses for the property
    def calculate_total_expenses(self):
        from django.db.models import Sum
        
        total_expenses = 0
        
        # Debugging: Print property details
        print(f"Calculating expenses for {self.address}")
        print(f"Mortgage: ${self.monthly_mortgage}")
        print(f"Property Type: {self.property_type}")
        
        # Base mortgage expense - ONLY for properties that are NOT owned outright
        # Owned Outright properties should not have mortgage expenses
        if self.property_type != 'owned_outright':
            # Base mortgage expense
            today = date.today()
            purchase_date = self.purchase_date
            months_owned = (today.year - purchase_date.year) * 12 + (today.month - purchase_date.month)
            
            if months_owned > 0:
                total_expenses += self.monthly_mortgage * months_owned
                print(f"Base Mortgage Expense: ${total_expenses}")
        else:
            print("No mortgage expense added (owned outright)")
        
        # Additional expense transactions for this property
        property_expenses = Transaction.objects.filter(
            property=self,
            transaction_type__in=['maintenance', 'taxes', 'insurance', 'other_expense']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Debugging: Print additional expenses
        print(f"Additional Expenses: ${property_expenses}")
        
        total_expenses += property_expenses
        print(f"Total Expenses: ${total_expenses}")
        
        return float(total_expenses)
    
    # Calculate net income for the property
    def calculate_net_income(self):
        return self.calculate_total_income() - self.calculate_total_expenses()
    
    # Property value prediction methods
    def calculate_current_value(self, annual_growth_rate=0.03):
        """Calculate current estimated value based on purchase price and growth rate"""
        if not self.purchase_price:
            return 0
        
        from datetime import date
        today = date.today()
        years_owned = (today.year - self.purchase_date.year) + \
                     (today.month - self.purchase_date.month) / 12
        
        if years_owned < 0:
            years_owned = 0
        
        # Convert all values to float for consistent calculation
        purchase_price_float = float(self.purchase_price)
        growth_rate_float = float(annual_growth_rate)
        years_owned_float = float(years_owned)
        
        # Calculate current value
        current_value = purchase_price_float * ((1 + growth_rate_float) ** years_owned_float)
        return round(current_value, 2)
    
    def calculate_future_value(self, years_ahead=5, annual_growth_rate=0.03):
        """Calculate future value based on current value and growth rate"""
        current_value = self.calculate_current_value(annual_growth_rate)
        if current_value == 0:
            return 0
        
        # Convert to float for calculation
        current_value_float = float(current_value)
        growth_rate_float = float(annual_growth_rate)
        years_ahead_float = float(years_ahead)
        
        future_value = current_value_float * ((1 + growth_rate_float) ** years_ahead_float)
        return round(future_value, 2)

    # Update calculate_roi method
    def calculate_roi(self, annual_growth_rate=0.03):
        """Calculate Return on Investment"""
        if not self.purchase_price:
            return 0
        
        current_value = self.calculate_current_value(annual_growth_rate)
        purchase_price_float = float(self.purchase_price)
        current_value_float = float(current_value)
        
        if purchase_price_float == 0:
            return 0
        
        roi = ((current_value_float - purchase_price_float) / purchase_price_float) * 100
        return round(roi, 2)

    # Update get_value_history method
    def get_value_history(self, years_back=5, annual_growth_rate=0.03):
        """Get value history for the past N years"""
        if not self.purchase_price:
            return []
        
        history = []
        from datetime import date
        today = date.today()
        
        for i in range(years_back, -1, -1):
            year = today.year - i
            years_since_purchase = year - self.purchase_date.year
            
            if years_since_purchase >= 0:
                # Convert to float for calculation
                purchase_price_float = float(self.purchase_price)
                growth_rate_float = float(annual_growth_rate)
                years_since_purchase_float = float(years_since_purchase)
                
                value = purchase_price_float * ((1 + growth_rate_float) ** years_since_purchase_float)
                
                # Calculate growth percentage compared to the previous year
                if len(history) > 0:
                    previous_value = history[-1]['value']
                    if previous_value != 0:
                        growth_percentage = ((value - previous_value) / previous_value) * 100
                    else:
                        growth_percentage = 0
                else:
                    growth_percentage = 0
                
                history.append({
                    'year': year,
                    'value': round(value, 2),
                    'growth': round(growth_percentage, 2)  # Add growth percentage
                })
        
        return history

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('rental_income', 'Rental Income'),
        ('additional_income', 'Additional Income'),
        ('maintenance', 'Maintenance'),
        ('taxes', 'Property Taxes'),
        ('insurance', 'Insurance'),
        ('other_expense', 'Other Expense'),
        ('other_income', 'Other Income'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Store as positive always
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type}: ${self.amount} on {self.date}"
    
class Scenario(models.Model):
    name = models.CharField(max_length=100)
    growth_rate = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.growth_rate}%)"