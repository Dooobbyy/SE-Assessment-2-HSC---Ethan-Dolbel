from django.db import models
from django.utils import timezone
from datetime import date
import calendar
from django.contrib.auth.models import AbstractUser, User
from django.db.models import Sum
import string
import secrets
from django.conf import settings
import uuid
from decimal import Decimal

class CustomUser(AbstractUser):
    # Add first_name and last_name explicitly if you want more control,
    # though AbstractUser already includes them. Ensure they are required in forms if needed.
    # first_name = models.CharField(max_length=150, blank=True) # Already in AbstractUser
    # last_name = models.CharField(max_length=150, blank=True)  # Already in AbstractUser
    # Your existing custom fields
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    # Email Verification Fields
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    # Password Reset Fields
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expires_at = models.DateTimeField(blank=True, null=True)

     # --- Fields for Email Change Confirmation ---
    email_change_token = models.CharField(max_length=100, blank=True, null=True)
    email_change_token_expires_at = models.DateTimeField(blank=True, null=True)
    email_change_new_email = models.EmailField(blank=True, null=True) # Store new email temporarily
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save()
        
    def generate_verification_token(self):
        """Generates a secure random token for email verification."""
        self.verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['verification_token'])
        
    def generate_reset_token(self, expiry_minutes=60):
        """Generates a secure random token for password reset with expiry."""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        self.save(update_fields=['reset_token', 'reset_token_expires_at'])
        
    def is_reset_token_valid(self):
        """Checks if the reset token is present and not expired."""
        if not self.reset_token or not self.reset_token_expires_at:
            return False
        return timezone.now() < self.reset_token_expires_at
        
    def __str__(self):
        return self.username
        
    class Meta(AbstractUser.Meta): # Inherit meta from AbstractUser
        # Ensure email addresses are unique across the entire user base
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email_constraint')
        ]

class Property(models.Model):
    PROPERTY_TYPES = [
        ('rental', 'Rental Property'),
        ('owner_occupied', 'Owner Occupied'),
        ('owned_outright', 'Owned Outright'),
    ]
    
    address = models.CharField(max_length=200)
    purchase_date = models.DateField()
    tenant_move_in_date = models.DateField(null=True, blank=True)
    tenant_move_out_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False, help_text="Original purchase price")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='rental')
    weekly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Weekly rental amount")
    weekly_mortgage = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Weekly mortgage payment")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add owner field to link property to user (corrected reference)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties')
    
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
        
    def calculate_total_income(self):
        
        total_income = Decimal('0.00')
        
        # Debugging: Print property details
        print(f"Calculating income for {self.address}")
        print(f"Weekly Rent: ${self.weekly_rent}")
        
        # Base rental income from tenants
        today = date.today()
        # FIX: Use 'tenants' instead of 'tenant_set' due to related_name
        for tenant in self.tenants.all():
            # Check if tenant was active during the period
            if tenant.move_in_date <= today:
                days_owned = (today - tenant.move_in_date).days
                weeks_owned = days_owned // 7
                
                if weeks_owned > 0:
                    total_income += Decimal(str(tenant.weekly_rent)) * weeks_owned
                    print(f"Income from tenant: ${total_income}")
        
        # Additional transactions for this property
        property_income_result = Transaction.objects.filter(
            property=self,
            transaction_type__in=['rental_income', 'additional_income', 'other_income']
        ).aggregate(Sum('amount'))['amount__sum']
        
        property_income = property_income_result or Decimal('0.00')
        
        # Debugging: Print additional income
        print(f"Additional Income: ${property_income}")
        
        total_income += property_income
        print(f"Total Income: ${total_income}")
        
        return float(total_income)

    # Calculate total expenses for the property
    def calculate_total_expenses(self):
        from datetime import date
        from decimal import Decimal
        
        total_expenses = Decimal('0.00')
        
        # Debugging: Print property details
        print(f"Calculating expenses for {self.address}")
        print(f"Weekly Mortgage: ${self.weekly_mortgage}")
        print(f"Property Type: {self.property_type}")
        
        # Base mortgage expense - ONLY for properties that are NOT owned outright
        # Owned Outright properties should not have mortgage expenses
        if self.property_type != 'owned_outright' and self.weekly_mortgage > 0:
            today = date.today()
            purchase_date = self.purchase_date
            
            # Calculate number of days owned
            days_owned = (today - purchase_date).days
            
            if days_owned > 0:
                # Calculate daily mortgage
                daily_mortgage = Decimal(str(self.weekly_mortgage)) / Decimal('7')
                total_expenses += daily_mortgage * days_owned
                print(f"Mortgage Expense: ${total_expenses}")
        
        # Additional expense transactions for this property
        property_expenses_result = Transaction.objects.filter(
            property=self,
            transaction_type__in=['maintenance', 'taxes', 'insurance', 'other_expense']
        ).aggregate(Sum('amount'))['amount__sum']
        
        property_expenses = property_expenses_result or Decimal('0.00')
        
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

class WeeklyRentChange(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    start_date = models.DateField()
    weekly_rent = models.DecimalField(max_digits=10, decimal_places=2)

class WeeklyMortgageChange(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    start_date = models.DateField()
    weekly_mortgage = models.DecimalField(max_digits=10, decimal_places=2)

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tenants')
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)
    weekly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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
    
    # Add owner field to link transaction to user
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    
    def __str__(self):
        return f"{self.transaction_type}: ${self.amount} on {self.date}"

class Scenario(models.Model):
    name = models.CharField(max_length=100)
    growth_rate = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add owner field to link scenario to user
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='scenarios')
    
    def __str__(self):
        return f"{self.name} ({self.growth_rate}%)"
    
class Alert(models.Model):
    ALERT = 'alert'
    REMINDER = 'reminder'
    TYPE_CHOICES = [
        (ALERT, 'Alert'),
        (REMINDER, 'Reminder'),
    ]

    # Use settings.AUTH_USER_MODEL for ForeignKey to custom user
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=ALERT)
    message = models.TextField(help_text="Enter your custom alert message here.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.user.username}] {self.type}: {self.message}"

    class Meta:
        ordering = ['-created_at']
