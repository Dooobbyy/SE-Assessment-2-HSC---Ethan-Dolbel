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
    
    # Property value prediction methods
    def calculate_current_value(self, annual_growth_rate=0.03):
        """Calculate current estimated value based on purchase price and growth rate"""
        if not self.purchase_price:
            return 0
        
        today = date.today()
        years_owned = (today.year - self.purchase_date.year) + \
                     (today.month - self.purchase_date.month) / 12
        
        if years_owned < 0:
            years_owned = 0
            
        current_value = float(self.purchase_price) * ((1 + annual_growth_rate) ** years_owned)
        return round(current_value, 2)
    
    def calculate_future_value(self, years_ahead=5, annual_growth_rate=0.03):
        """Calculate future value based on current value and growth rate"""
        current_value = self.calculate_current_value(annual_growth_rate)
        if current_value == 0:
            return 0
            
        future_value = current_value * ((1 + annual_growth_rate) ** years_ahead)
        return round(future_value, 2)
    
    def get_value_history(self, years_back=5, annual_growth_rate=0.03):
        """Get value history for the past N years"""
        if not self.purchase_price:
            return []
        
        history = []
        today = date.today()
        
        for i in range(years_back, -1, -1):
            year = today.year - i
            years_since_purchase = year - self.purchase_date.year
            
            if years_since_purchase >= 0:
                value = float(self.purchase_price) * ((1 + annual_growth_rate) ** years_since_purchase)
                history.append({
                    'year': year,
                    'value': round(value, 2)
                })
        
        return history
    
    def calculate_roi(self, annual_growth_rate=0.03):
        """Calculate Return on Investment"""
        if not self.purchase_price:
            return 0
        
        current_value = self.calculate_current_value(annual_growth_rate)
        roi = ((current_value - float(self.purchase_price)) / float(self.purchase_price)) * 100
        return round(roi, 2)

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