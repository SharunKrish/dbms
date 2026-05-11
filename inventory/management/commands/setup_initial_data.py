from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = (
        "Sets up initial data for the WIMS application, including a default admin user."
    )

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser(
                "admin", "admin@example.com", "adminpassword"
            )
            admin_user.role = "ADMIN"
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully created default admin user (admin / adminpassword)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists."))
