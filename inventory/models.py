from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce


class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("STAFF", "Staff"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == "ADMIN" or self.is_superuser

    @property
    def is_manager(self):
        return self.role in ("ADMIN", "MANAGER") or self.is_superuser


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)  # Soft delete

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def stock_on_hand(self):
        """
        Computes current stock level using the formula from SRS:
        S_final = S_initial(0) + Σ(TransactionsIN) - Σ(TransactionsOUT)
        """
        result = self.transactions.aggregate(
            inbound=Coalesce(
                Sum("quantity", filter=Q(transaction_type="IN")), 0
            ),
            outbound=Coalesce(
                Sum("quantity", filter=Q(transaction_type="OUT")), 0
            ),
        )
        return result["inbound"] - result["outbound"]

    @property
    def is_low_stock(self):
        return self.stock_on_hand <= self.min_stock


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
    notes = models.TextField(blank=True, help_text="Optional reference or audit note.")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.get_transaction_type_display()} - "
            f"{self.quantity} x {self.product.name} "
            f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}]"
        )
