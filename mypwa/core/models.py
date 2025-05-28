from django.db import models

# Create your models here.

class Property(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.name


class Income(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.property} - ${self.amount}"


class Expense(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.property} - {self.category}"