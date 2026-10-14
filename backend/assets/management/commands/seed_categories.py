from django.core.management.base import BaseCommand

from assets.models import Category, SubCategory

CATEGORIES = {
    ("Vehicles", "VEH"): ["Car", "Lorry", "Motorbike"],
    ("IT Equipment", "ITE"): [
        "Laptop", "Smartphone", "Mobile Phone", "Landline",
        "Printer", "Thermal Printer", "SIM Card",
    ],
    ("Fuel Cards", "FUE"): ["Fuel Card"],
}


class Command(BaseCommand):
    help = "Create the standard asset categories and sub-categories (safe to repeat)."

    def handle(self, *args, **options):
        created_count = 0
        for (name, code), subcategories in CATEGORIES.items():
            category, created = Category.objects.get_or_create(
                name=name, defaults={"code": code}
            )
            created_count += created
            for sub_name in subcategories:
                _, created = SubCategory.objects.get_or_create(
                    category=category, name=sub_name
                )
                created_count += created
        self.stdout.write(self.style.SUCCESS(f"Done. {created_count} new records created."))
