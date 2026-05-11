from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Supplier, Product, Transaction


class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (("Role Information", {"fields": ("role",)}),)
    list_display = ["username", "email", "role", "is_staff"]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Transaction)
