# core/admin.py
from django.contrib import admin
from .models import Property, Transaction

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('address', 'purchase_date', 'monthly_rent', 'created_at')
    list_filter = ('purchase_date',)
    search_fields = ('address',)
    ordering = ('-purchase_date',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('property', 'transaction_type', 'amount', 'date', 'description')
    list_filter = ('transaction_type', 'date', 'property')
    search_fields = ('description',)
    date_hierarchy = 'date'
    ordering = ('-date',)