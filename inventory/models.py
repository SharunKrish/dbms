from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("STAFF", "Staff"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.company_name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)  # Soft delete

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPE_CHOICES = (
        ("IN", "Inbound (Restock)"),
        ("OUT", "Outbound (Dispatch)"),
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="transactions"
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="transactions"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.quantity} of {self.product.name} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
