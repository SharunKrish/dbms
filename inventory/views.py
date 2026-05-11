import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Q, F, IntegerField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .models import Product, Supplier, Transaction, User
from .forms import (
    ProductForm,
    SupplierForm,
    TransactionInboundForm,
    TransactionOutboundForm,
    CustomUserCreationForm,
)


def get_annotated_products():
    return Product.objects.filter(is_active=True).annotate(
        inbound=Coalesce(
            Sum(
                "transactions__quantity", filter=Q(transactions__transaction_type="IN")
            ),
            0,
            output_field=IntegerField(),
        ),
        outbound=Coalesce(
            Sum(
                "transactions__quantity", filter=Q(transactions__transaction_type="OUT")
            ),
            0,
            output_field=IntegerField(),
        ),
        stock_on_hand=F("inbound") - F("outbound"),
    )


class CustomLoginView(LoginView):
    template_name = "inventory/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


@login_required
def dashboard(request):
    products = get_annotated_products()
    low_stock_items = [p for p in products if p.stock_on_hand <= p.min_stock]
    total_products = products.count()
    recent_transactions = Transaction.objects.order_by("-timestamp")[:10]

    context = {
        "total_products": total_products,
        "low_stock_count": len(low_stock_items),
        "low_stock_items": low_stock_items,
        "recent_transactions": recent_transactions,
    }
    return render(request, "inventory/dashboard.html", context)


# --- Product Views ---
@login_required
def product_list(request):
    query = request.GET.get("q", "")
    products_qs = get_annotated_products().order_by("name")
    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

    paginator = Paginator(products_qs, 10)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    return render(
        request, "inventory/product_list.html", {"products": products, "query": query}
    )


@login_required
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
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if request.method == "POST":
        product.is_active = False
        product.save()
        messages.success(request, "Product deleted successfully.")
        return redirect("product_list")
    return render(
        request, "inventory/product_confirm_delete.html", {"product": product}
    )


# --- Supplier Views ---
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by("company_name")
    return render(request, "inventory/supplier_list.html", {"suppliers": suppliers})


@login_required
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


# --- User Management Views (Admin Only) ---
def is_admin(user):
    return user.is_authenticated and (user.role == "ADMIN" or user.is_superuser)


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


# --- Transaction Views ---
@login_required
def transaction_list(request):
    transactions = Transaction.objects.order_by("-timestamp")
    paginator = Paginator(transactions, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "inventory/transaction_list.html", {"page_obj": page_obj})


@login_required
def transaction_inbound(request):
    if request.method == "POST":
        form = TransactionInboundForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.transaction_type = "IN"
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Inbound transaction recorded.")
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
            transaction = form.save(commit=False)
            product = get_annotated_products().get(pk=transaction.product.pk)
            if transaction.quantity > product.stock_on_hand:
                form.add_error(
                    "quantity",
                    f"Cannot dispatch {transaction.quantity}. Only {product.stock_on_hand} in stock.",
                )
            else:
                transaction.transaction_type = "OUT"
                transaction.user = request.user
                transaction.save()
                messages.success(request, "Outbound transaction recorded.")
                return redirect("transaction_list")
    else:
        form = TransactionOutboundForm()
    return render(
        request,
        "inventory/transaction_form.html",
        {"form": form, "title": "Dispatch (Outbound)"},
    )


# --- Reporting ---
@login_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="inventory_transactions.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(
        ["ID", "Type", "Product", "Quantity", "User", "Supplier", "Timestamp"]
    )

    transactions = Transaction.objects.all().order_by("-timestamp")
    for tx in transactions:
        writer.writerow(
            [
                tx.id,
                tx.get_transaction_type_display(),
                tx.product.name,
                tx.quantity,
                tx.user.username,
                tx.supplier.company_name if tx.supplier else "N/A",
                tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
    return response
