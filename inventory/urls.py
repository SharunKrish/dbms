from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Products (FR-02)
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_create, name="product_create"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/edit/", views.product_update, name="product_update"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),

    # Categories
    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_update, name="category_update"),

    # Suppliers
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/add/", views.supplier_create, name="supplier_create"),
    path("suppliers/<int:pk>/edit/", views.supplier_update, name="supplier_update"),

    # Transactions (FR-03)
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/in/", views.transaction_inbound, name="transaction_inbound"),
    path("transactions/out/", views.transaction_outbound, name="transaction_outbound"),

    # User Management (FR-01)
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_update, name="user_update"),
    path("users/<int:pk>/deactivate/", views.user_deactivate, name="user_deactivate"),

    # Reporting (SRS §6)
    path("export/csv/", views.export_csv, name="export_csv"),
]
