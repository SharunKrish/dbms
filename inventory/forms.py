from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Supplier, Transaction, User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + (
            "email",
            "role",
        )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["sku", "name", "description", "category", "unit_price", "min_stock"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["company_name", "contact_person", "email"]


class TransactionInboundForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["product", "supplier", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].required = True


class TransactionOutboundForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["product", "quantity"]
