from django.contrib import admin
from .models import Property, Income, Expense

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'purchase_price')

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('property', 'date', 'amount', 'description')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('property', 'date', 'category', 'amount')