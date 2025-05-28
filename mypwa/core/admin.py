from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Property, Income, Expense

admin.site.register(Property)
admin.site.register(Income)
admin.site.register(Expense)