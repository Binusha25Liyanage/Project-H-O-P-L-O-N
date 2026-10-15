from django.core.management.base import BaseCommand

from assets.models import Category, DetailType, SubCategory

V, IT, SIM, FUEL = (
    DetailType.VEHICLE, DetailType.IT_DEVICE, DetailType.SIM, DetailType.FUEL_CARD,
)

CATEGORIES = {
    ("Vehicles", "VEH"): [("Car", V), ("Lorry", V), ("Motorbike", V)],
    ("IT Equipment", "ITE"): [
        ("Laptop", IT), ("Smartphone", IT), ("Mobile Phone", IT), ("Landline", IT),
        ("Printer", IT), ("Thermal Printer", IT), ("SIM Card", SIM),
    ],
    ("Fuel Cards", "FUE"): [("Fuel Card", FUEL)],
}


class Command(BaseCommand):
    help = (
        "Create the standard asset categories and sub-categories, and set the "
        "detail type of sub-categories that don't have one yet. Safe to repeat."
    )

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for (name, code), subcategories in CATEGORIES.items():
            category, created = Category.objects.get_or_create(
                name=name, defaults={"code": code}
            )
            created_count += created
            for sub_name, detail_type in subcategories:
                sub, created = SubCategory.objects.get_or_create(
                    category=category, name=sub_name,
                    defaults={"detail_type": detail_type},
                )
                created_count += created
                if not created and sub.detail_type == DetailType.NONE:
                    sub.detail_type = detail_type
                    sub.save(update_fields=["detail_type"])
                    updated_count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Done. {created_count} new records created, {updated_count} updated."
        ))
