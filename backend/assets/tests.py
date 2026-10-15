import re
from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import Role, User
from employees.models import Department, Location

from .models import Asset, AssetStatus, Category, DetailType, SubCategory

PASSWORD = "Str0ng-Pass-12345"


class AssetsApiTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            "super1", password=PASSWORD, role=Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            "admin1", password=PASSWORD, role=Role.ADMIN
        )
        self.normal_user = User.objects.create_user(
            "user1", password=PASSWORD, role=Role.USER
        )
        self.location = Location.objects.create(name="Head Office")
        self.department = Department.objects.create(name="IT")
        self.vehicles = Category.objects.create(name="Vehicles", code="VEH")
        self.it = Category.objects.create(name="IT Equipment", code="ITE")
        self.car = SubCategory.objects.create(category=self.vehicles, name="Car")
        self.laptop = SubCategory.objects.create(category=self.it, name="Laptop")

    def payload(self, **overrides):
        data = {
            "category": self.it.id,
            "subcategory": self.laptop.id,
            "name": "Dell Latitude 5440",
            "purchase_date": "2026-01-15",
            "purchase_cost": "250000.00",
            "supplier": "Dell Lanka",
            "location": self.location.id,
        }
        data.update(overrides)
        return data

    def make_asset(self, **overrides):
        data = {
            "category": self.it,
            "subcategory": self.laptop,
            "name": "Existing laptop",
            "purchase_cost": Decimal("100000.00"),
            "location": self.location,
        }
        data.update(overrides)
        return Asset.objects.create(**data)

    # Categories
    def test_super_admin_can_create_category(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.post(
            "/api/v1/categories/", {"name": "Furniture", "code": "fur"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["code"], "FUR")

    def test_admin_can_read_but_not_create_category(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/v1/categories/").status_code, 200)
        response = self.client.post(
            "/api/v1/categories/", {"name": "Furniture", "code": "FUR"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_duplicate_category_code_rejected_in_any_case(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.post(
            "/api/v1/categories/", {"name": "Other", "code": "veh"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_category_code_cannot_be_changed(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(
            f"/api/v1/categories/{self.it.id}/", {"code": "NEW"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_seed_sets_detail_types_and_fixes_existing_ones(self):
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        call_command("seed_categories")
        types = {s.name: s.detail_type for s in SubCategory.objects.all()}
        self.assertEqual(types["Car"], DetailType.VEHICLE)
        self.assertEqual(types["Laptop"], DetailType.IT_DEVICE)
        self.assertEqual(types["SIM Card"], DetailType.SIM)
        self.assertEqual(types["Fuel Card"], DetailType.FUEL_CARD)
        # A sub-category created before detail types existed gets fixed
        SubCategory.objects.filter(name="Laptop").update(detail_type=DetailType.NONE)
        call_command("seed_categories")
        self.assertEqual(
            SubCategory.objects.get(name="Laptop").detail_type, DetailType.IT_DEVICE
        )

    def test_detail_type_cannot_change_while_assets_exist(self):
        self.make_asset()
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(
            f"/api/v1/subcategories/{self.laptop.id}/",
            {"detail_type": DetailType.SIM},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_detail_type_can_be_set_when_no_assets_use_it(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(
            f"/api/v1/subcategories/{self.car.id}/",
            {"detail_type": DetailType.VEHICLE},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail_type"], DetailType.VEHICLE)

    def test_duplicate_subcategory_in_same_category_rejected(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.post(
            "/api/v1/subcategories/",
            {"category": self.it.id, "name": "Laptop"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_deactivate_category_with_live_assets(self):
        self.make_asset()
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(
            f"/api/v1/categories/{self.it.id}/", {"is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_seed_command_is_repeatable(self):
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        call_command("seed_categories")
        first_count = SubCategory.objects.count()
        call_command("seed_categories")
        self.assertEqual(SubCategory.objects.count(), first_count)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(first_count, 11)

    # Assets
    def test_admin_creates_asset_with_automatic_id(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/assets/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertRegex(response.data["asset_id"], r"^AST-\d{6}$")
        asset = Asset.objects.get(pk=response.data["id"])
        self.assertEqual(asset.asset_id, f"AST-{asset.pk:06d}")
        self.assertEqual(response.data["status"], AssetStatus.IN_STOCK)
        self.assertEqual(Decimal(response.data["current_value"]), Decimal("250000.00"))
        self.assertEqual(response.data["created_by_username"], "admin1")

    def test_normal_user_cannot_list_assets(self):
        self.client.force_authenticate(self.normal_user)
        self.assertEqual(self.client.get("/api/v1/assets/").status_code, 403)

    def test_subcategory_must_match_category(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/assets/", self.payload(subcategory=self.car.id), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_change_category_after_creation(self):
        asset = self.make_asset()
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/assets/{asset.id}/",
            {"category": self.vehicles.id, "subcategory": self.car.id},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_set_assigned_or_disposed_by_hand(self):
        self.client.force_authenticate(self.admin)
        for status in (AssetStatus.ASSIGNED, AssetStatus.DISPOSED):
            response = self.client.post(
                "/api/v1/assets/", self.payload(status=status), format="json"
            )
            self.assertEqual(response.status_code, 400, status)

    def test_admin_can_mark_asset_lost(self):
        asset = self.make_asset()
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/assets/{asset.id}/", {"status": AssetStatus.LOST}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_assigned_asset_status_cannot_be_changed(self):
        asset = self.make_asset(status=AssetStatus.ASSIGNED)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/assets/{asset.id}/",
            {"status": AssetStatus.IN_STOCK},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_disposed_asset_cannot_be_edited(self):
        asset = self.make_asset(status=AssetStatus.DISPOSED)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/assets/{asset.id}/", {"notes": "late note"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_negative_cost_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/assets/", self.payload(purchase_cost="-5"), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_future_purchase_date_rejected(self):
        future = (timezone.localdate() + timedelta(days=5)).isoformat()
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/assets/", self.payload(purchase_date=future), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_warranty_before_purchase_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/assets/",
            self.payload(warranty_end_date="2025-01-01"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_inactive_location_rejected(self):
        self.location.is_active = False
        self.location.save()
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/assets/", self.payload(), format="json")
        self.assertEqual(response.status_code, 400)

    def test_filter_by_status_and_search_by_name(self):
        self.make_asset(name="Spare laptop")
        self.make_asset(name="Broken laptop", status=AssetStatus.UNDER_REPAIR)
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/assets/?status=UNDER_REPAIR")
        self.assertEqual(response.data["count"], 1)
        response = self.client.get("/api/v1/assets/?search=Spare")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Spare laptop")
