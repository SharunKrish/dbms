import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction as db_transaction
from django.db.models import Sum, Q, F, IntegerField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .models import Product, Supplier, Transaction, User, Category
from .forms import (
    ProductForm,
    SupplierForm,
    TransactionInboundForm,
    TransactionOutboundForm,
    CustomUserCreationForm,
    CustomUserChangeForm,
    CategoryForm,
)


# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------

def is_admin(user):
    return user.is_authenticated and (user.role == "ADMIN" or user.is_superuser)


def is_manager_or_above(user):
    return user.is_authenticated and (user.role in ("ADMIN", "MANAGER") or user.is_superuser)


# ---------------------------------------------------------------------------
# Stock annotation helper — used across multiple views
# ---------------------------------------------------------------------------

def get_annotated_products(active_only=True):
    """
    Returns a queryset of Products annotated with:
      - inbound  : total IN quantity
      - outbound : total OUT quantity
      - stock_on_hand : inbound - outbound  (S_final per SRS FR-03)
    """
    qs = Product.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)

    return qs.annotate(
        inbound=Coalesce(
            Sum("transactions__quantity", filter=Q(transactions__transaction_type="IN")),
            0,
            output_field=IntegerField(),
        ),
        outbound=Coalesce(
            Sum("transactions__quantity", filter=Q(transactions__transaction_type="OUT")),
            0,
            output_field=IntegerField(),
        ),
        stock_on_hand=F("inbound") - F("outbound"),
    )


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

class CustomLoginView(LoginView):
    template_name = "inventory/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    products = get_annotated_products()
    low_stock_items = [p for p in products if p.stock_on_hand <= p.min_stock]
    total_products = products.count()
    total_suppliers = Supplier.objects.count()
    recent_transactions = Transaction.objects.select_related(
        "product", "user", "supplier"
    ).order_by("-timestamp")[:10]

    context = {
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "low_stock_count": len(low_stock_items),
        "low_stock_items": low_stock_items,
        "recent_transactions": recent_transactions,
    }
    return render(request, "inventory/dashboard.html", context)


# ---------------------------------------------------------------------------
# Product Views
# ---------------------------------------------------------------------------

@login_required
def product_list(request):
    query = request.GET.get("q", "").strip()
    products_qs = get_annotated_products().order_by("name")
    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(category__name__icontains=query)
        )

    paginator = Paginator(products_qs, 10)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    return render(
        request,
        "inventory/product_list.html",
        {"products": products, "query": query},
    )


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    transactions = Transaction.objects.filter(product=product).select_related(
        "user", "supplier"
    ).order_by("-timestamp")

    paginator = Paginator(transactions, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "product": product,
        "page_obj": page_obj,
        "stock_on_hand": product.stock_on_hand,
    }
    return render(request, "inventory/product_detail.html", context)


@login_required
@user_passes_test(is_manager_or_above)
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product created successfully.")
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(
        request, "inventory/product_form.html", {"form": form, "title": "Add Product"}
    )


@login_required
@user_passes_test(is_manager_or_above)
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(
        request, "inventory/product_form.html", {"form": form, "title": "Edit Product"}
    )


@login_required
@user_passes_test(is_admin)
def product_delete(request, pk):
    """Soft delete — preserves transaction history (SRS FR-02)."""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if request.method == "POST":
        product.is_active = False
        product.save()
        messages.success(request, f'Product "{product.name}" has been deactivated.')
        return redirect("product_list")
    return render(
        request, "inventory/product_confirm_delete.html", {"product": product}
    )


# ---------------------------------------------------------------------------
# Category Views
# ---------------------------------------------------------------------------

@login_required
def category_list(request):
    categories = Category.objects.all().order_by("name")
    return render(request, "inventory/category_list.html", {"categories": categories})


@login_required
@user_passes_test(is_manager_or_above)
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect("category_list")
    else:
        form = CategoryForm()
    return render(
        request, "inventory/category_form.html", {"form": form, "title": "Add Category"}
    )


@login_required
@user_passes_test(is_manager_or_above)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)
    return render(
        request, "inventory/category_form.html", {"form": form, "title": "Edit Category"}
    )


# ---------------------------------------------------------------------------
# Supplier Views
# ---------------------------------------------------------------------------

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by("company_name")
    return render(request, "inventory/supplier_list.html", {"suppliers": suppliers})


@login_required
@user_passes_test(is_manager_or_above)
def supplier_create(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added successfully.")
            return redirect("supplier_list")
    else:
        form = SupplierForm()
    return render(
        request, "inventory/supplier_form.html", {"form": form, "title": "Add Supplier"}
    )


@login_required
@user_passes_test(is_manager_or_above)
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier updated successfully.")
            return redirect("supplier_list")
    else:
        form = SupplierForm(instance=supplier)
    return render(
        request,
        "inventory/supplier_form.html",
        {"form": form, "title": "Edit Supplier"},
    )


# ---------------------------------------------------------------------------
# User Management Views (Admin Only) — RBAC FR-01
# ---------------------------------------------------------------------------

@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by("username")
    return render(request, "inventory/user_list.html", {"users": users})


@user_passes_test(is_admin)
def user_create(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("user_list")
    else:
        form = CustomUserCreationForm()
    return render(
        request, "inventory/user_form.html", {"form": form, "title": "Add User"}
    )


@user_passes_test(is_admin)
def user_update(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("user_list")
    else:
        form = CustomUserChangeForm(instance=user_obj)
    return render(
        request, "inventory/user_form.html", {"form": form, "title": "Edit User"}
    )


@user_passes_test(is_admin)
def user_deactivate(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user_obj.is_active = False
        user_obj.save()
        messages.success(request, f'User "{user_obj.username}" has been deactivated.')
        return redirect("user_list")
    return render(
        request, "inventory/user_confirm_deactivate.html", {"user_obj": user_obj}
    )


# ---------------------------------------------------------------------------
# Transaction Views — ACID atomic() wrapping (SRS §5.1)
# ---------------------------------------------------------------------------

@login_required
def transaction_list(request):
    transactions = Transaction.objects.select_related(
        "product", "user", "supplier"
    ).order_by("-timestamp")
    paginator = Paginator(transactions, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "inventory/transaction_list.html", {"page_obj": page_obj})


@login_required
def transaction_inbound(request):
    if request.method == "POST":
        form = TransactionInboundForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                txn = form.save(commit=False)
                txn.transaction_type = "IN"
                txn.user = request.user
                txn.save()
            messages.success(request, f"Inbound: {txn.quantity} unit(s) of '{txn.product.name}' recorded.")
            return redirect("transaction_list")
    else:
        form = TransactionInboundForm()
    return render(
        request,
        "inventory/transaction_form.html",
        {"form": form, "title": "Restock (Inbound)"},
    )


@login_required
def transaction_outbound(request):
    if request.method == "POST":
        form = TransactionOutboundForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            # Re-fetch stock_on_hand inside atomic block to prevent race conditions
            with db_transaction.atomic():
                product = (
                    get_annotated_products()
                    .select_for_update()
                    .get(pk=txn.product.pk)
                )
                if txn.quantity > product.stock_on_hand:
                    form.add_error(
                        "quantity",
                        f"Cannot dispatch {txn.quantity} unit(s). "
                        f"Only {product.stock_on_hand} in stock.",
                    )
                else:
                    txn.transaction_type = "OUT"
                    txn.user = request.user
                    txn.save()
                    messages.success(
                        request,
                        f"Outbound: {txn.quantity} unit(s) of '{txn.product.name}' dispatched.",
                    )
                    return redirect("transaction_list")
    else:
        form = TransactionOutboundForm()
    return render(
        request,
        "inventory/transaction_form.html",
        {"form": form, "title": "Dispatch (Outbound)"},
    )


# ---------------------------------------------------------------------------
# Reporting — CSV export with month/year filter (SRS §6)
# ---------------------------------------------------------------------------

@login_required
def export_csv(request):
    month = request.GET.get("month")
    year = request.GET.get("year")

    response = HttpResponse(content_type="text/csv")
    filename = "inventory_transactions.csv"
    if month and year:
        filename = f"inventory_transactions_{year}_{month:0>2}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Type", "Product", "SKU", "Quantity", "User", "Supplier", "Notes", "Timestamp"])

    transactions = Transaction.objects.select_related(
        "product", "user", "supplier"
    ).order_by("-timestamp")
    if month and year:
        transactions = transactions.filter(
            timestamp__year=int(year), timestamp__month=int(month)
        )

    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.get_transaction_type_display(),
            tx.product.name,
            tx.product.sku,
            tx.quantity,
            tx.user.username,
            tx.supplier.company_name if tx.supplier else "N/A",
            tx.notes,
            tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        ])
    return response
