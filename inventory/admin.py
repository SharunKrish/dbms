from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Supplier, Product, Transaction


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ("Role Information", {"fields": ("role",)}),
    )
    list_display = ["username", "email", "role", "is_active", "is_staff", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "email"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["company_name", "contact_person", "email", "phone"]
    search_fields = ["company_name", "contact_person", "email"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "category", "unit_price", "min_stock", "is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["sku", "name"]
    readonly_fields = ["is_active"]  # Protect soft-delete field from accidental changes
    actions = ["soft_delete_products"]

    @admin.action(description="Soft-delete selected products")
    def soft_delete_products(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} product(s) deactivated.")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction_type", "product", "quantity", "user", "supplier", "timestamp"]
    list_filter = ["transaction_type", "timestamp"]
    search_fields = ["product__name", "product__sku", "user__username", "supplier__company_name"]
    readonly_fields = ["transaction_type", "product", "quantity", "user", "supplier", "timestamp", "notes"]
    # Transactions are immutable audit records — no adding/editing via admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
