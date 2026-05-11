from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Product, Supplier, Transaction, User, Category


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "role")


class CustomUserChangeForm(UserChangeForm):
    password = None  # Hide raw password hash from edit form

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("username", "email", "role", "is_active")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["sku", "name", "description", "category", "unit_price", "min_stock"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "min_stock": "Alert threshold — dashboard will highlight when stock falls at or below this level.",
            "sku": "Stock Keeping Unit — must be unique per product.",
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["company_name", "contact_person", "email", "phone"]
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+91 98765 43210"}),
        }


class TransactionInboundForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["product", "supplier", "quantity", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "e.g. Purchase Order #PO-2024-001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].required = True
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")


class TransactionOutboundForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["product", "quantity", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "e.g. Dispatch Order #DO-2024-055"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")
