from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Category, Supplier, Product


class Command(BaseCommand):
    help = "Seeds WIMS with a default admin user, sample categories, suppliers, and products."

    def handle(self, *args, **options):
        User = get_user_model()

        # -- Admin User -------------------------------------------------------
        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser(
                "admin", "admin@wims.local", "adminpassword"
            )
            admin_user.role = "ADMIN"
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created admin user  (admin / adminpassword)"))
        else:
            self.stdout.write(self.style.WARNING("[--] Admin user already exists - skipped."))

        # -- Sample Manager & Staff -------------------------------------------
        if not User.objects.filter(username="manager1").exists():
            mgr = User.objects.create_user("manager1", "manager@wims.local", "managerpassword")
            mgr.role = "MANAGER"
            mgr.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created manager1  (manager1 / managerpassword)"))

        if not User.objects.filter(username="staff1").exists():
            st = User.objects.create_user("staff1", "staff@wims.local", "staffpassword")
            st.role = "STAFF"
            st.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created staff1    (staff1 / staffpassword)"))

        # -- Categories -------------------------------------------------------
        categories_data = [
            ("Electronics",    "Consumer and industrial electronic components"),
            ("Packaging",      "Boxes, wrapping materials, and containers"),
            ("Raw Materials",  "Unprocessed goods used in manufacturing"),
            ("Office Supplies","Stationery and general office consumables"),
            ("Machinery Parts","Spare parts and components for warehouse equipment"),
        ]
        categories = {}
        for name, desc in categories_data:
            cat, created = Category.objects.get_or_create(name=name, defaults={"description": desc})
            categories[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"[OK] Category: {name}"))

        # -- Suppliers --------------------------------------------------------
        suppliers_data = [
            ("TechSource Pvt Ltd", "Arun Nair",     "arun@techsource.in",    "+91 98001 11001"),
            ("PackPro India",      "Meena Iyer",    "meena@packpro.in",      "+91 98002 22002"),
            ("RawMat Corp",        "Suresh Pillai", "suresh@rawmat.com",     "+91 98003 33003"),
            ("OfficeDirect",       "Priya Menon",   "priya@officedirect.in", "+91 98004 44004"),
        ]
        suppliers = {}
        for company, person, email, phone in suppliers_data:
            sup, created = Supplier.objects.get_or_create(
                company_name=company,
                defaults={"contact_person": person, "email": email, "phone": phone},
            )
            suppliers[company] = sup
            if created:
                self.stdout.write(self.style.SUCCESS(f"[OK] Supplier: {company}"))

        # -- Products ---------------------------------------------------------
        products_data = [
            ("SKU-ELEC-001", "Arduino Uno R3",         "Electronics",    12.50,  10),
            ("SKU-ELEC-002", "Raspberry Pi 4 (4GB)",   "Electronics",    55.00,   5),
            ("SKU-ELEC-003", "DC Motor 12V",            "Electronics",     4.75,  20),
            ("PKG-BOX-001",  "Cardboard Box (Medium)",  "Packaging",       0.85,  50),
            ("PKG-BOX-002",  "Bubble Wrap Roll (10m)",  "Packaging",       3.20,  15),
            ("RAW-STL-001",  "Steel Rod 1m",            "Raw Materials",   2.40,  30),
            ("RAW-PLY-001",  "Plywood Sheet 8x4ft",     "Raw Materials",  18.00,  10),
            ("OFF-PEN-001",  "Ballpoint Pen (Blue)",    "Office Supplies",  0.15, 100),
            ("OFF-A4-001",   "A4 Paper Ream (500)",     "Office Supplies",  4.50,  25),
            ("MCH-BRG-001",  "Ball Bearing 6205",       "Machinery Parts",  1.80,  40),
        ]

        for sku, name, cat_name, price, min_stock in products_data:
            prod, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": categories.get(cat_name),
                    "unit_price": price,
                    "min_stock": min_stock,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"[OK] Product: {name}  [{sku}]"))

        self.stdout.write(self.style.SUCCESS("\n[DONE] Initial data setup complete."))
