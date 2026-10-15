from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import Role, User
from assets.models import Asset, Category, SubCategory
from employees.models import Location

from .models import VehicleDetails

PASSWORD = "Str0ng-Pass-12345"


class VehicleDetailsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "admin1", password=PASSWORD, role=Role.ADMIN
        )
        self.location = Location.objects.create(name="Head Office")
        self.vehicles = Category.objects.create(name="Vehicles", code="VEH")
        self.it = Category.objects.create(name="IT Equipment", code="ITE")
        self.car = SubCategory.objects.create(category=self.vehicles, name="Car")
        self.laptop = SubCategory.objects.create(category=self.it, name="Laptop")
        self.client.force_authenticate(self.admin)

    def details(self, **overrides):
        data = {
            "registration_number": "cab-1234",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "chassis_number": "ch-0001",
            "engine_number": "en-0001",
            "fuel_type": "PETROL",
            "colour": "White",
            "odometer_km": 12000,
            "insurance_expiry": "2027-03-31",
            "revenue_licence_expiry": "2027-01-31",
        }
        data.update(overrides)
        return data

    def payload(self, **overrides):
        data = {
            "category": self.vehicles.id,
            "subcategory": self.car.id,
            "name": "Sales car",
            "purchase_cost": "6500000.00",
            "location": self.location.id,
            "details": self.details(),
        }
        data.update(overrides)
        return data

    def create_vehicle(self, **detail_overrides):
        response = self.client.post(
            "/api/v1/assets/",
            self.payload(details=self.details(**detail_overrides)),
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_create_vehicle_with_details(self):
        data = self.create_vehicle()
        self.assertEqual(data["details"]["registration_number"], "CAB-1234")
        self.assertEqual(data["details"]["chassis_number"], "CH-0001")
        self.assertEqual(data["details"]["make"], "Toyota")
        self.assertRegex(data["asset_id"], r"^AST-\d{6}$")
        self.assertEqual(VehicleDetails.objects.count(), 1)

    def test_vehicle_without_details_rejected(self):
        payload = self.payload()
        del payload["details"]
        response = self.client.post("/api/v1/assets/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("details", response.data)
        self.assertEqual(Asset.objects.count(), 0)

    def test_missing_detail_field_rejected_and_no_asset_left_behind(self):
        details = self.details()
        del details["make"]
        response = self.client.post(
            "/api/v1/assets/", self.payload(details=details), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("make", response.data["details"])
        self.assertEqual(Asset.objects.count(), 0)

    def test_duplicate_registration_number_rejected_in_any_case(self):
        self.create_vehicle()
        response = self.client.post(
            "/api/v1/assets/",
            self.payload(
                details=self.details(registration_number="CAB-1234", chassis_number="X-2")
            ),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("registration_number", response.data["details"])
        self.assertEqual(Asset.objects.count(), 1)

    def test_duplicate_chassis_number_rejected(self):
        self.create_vehicle()
        response = self.client.post(
            "/api/v1/assets/",
            self.payload(
                details=self.details(registration_number="CAB-9999", chassis_number="ch-0001")
            ),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("chassis_number", response.data["details"])

    def test_invalid_year_rejected(self):
        response = self.client.post(
            "/api/v1/assets/",
            self.payload(details=self.details(year=1900)),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_details_not_accepted_for_category_without_details_yet(self):
        response = self.client.post(
            "/api/v1/assets/",
            {
                "category": self.it.id,
                "subcategory": self.laptop.id,
                "name": "Laptop",
                "location": self.location.id,
                "details": {"anything": 1},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("details", response.data)

    def test_retrieve_and_list_include_details(self):
        data = self.create_vehicle()
        one = self.client.get(f"/api/v1/assets/{data['id']}/")
        self.assertEqual(one.data["details"]["model"], "Corolla")
        many = self.client.get("/api/v1/assets/")
        self.assertEqual(many.data["results"][0]["details"]["model"], "Corolla")

    def test_patch_details_partially(self):
        data = self.create_vehicle()
        response = self.client.patch(
            f"/api/v1/assets/{data['id']}/",
            {"details": {"odometer_km": 15000, "colour": "Silver"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["details"]["odometer_km"], 15000)
        self.assertEqual(response.data["details"]["colour"], "Silver")
        self.assertEqual(response.data["details"]["make"], "Toyota")

    def test_odometer_cannot_go_down(self):
        data = self.create_vehicle()
        response = self.client.patch(
            f"/api/v1/assets/{data['id']}/",
            {"details": {"odometer_km": 100}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("odometer_km", response.data["details"])

    def test_own_registration_number_can_be_resubmitted_on_update(self):
        data = self.create_vehicle()
        response = self.client.patch(
            f"/api/v1/assets/{data['id']}/",
            {"details": {"registration_number": "cab-1234"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_search_by_registration_number(self):
        self.create_vehicle()
        response = self.client.get("/api/v1/assets/?search=CAB-1234")
        self.assertEqual(response.data["count"], 1)

    def test_vehicle_asset_without_details_can_still_be_edited(self):
        asset = Asset.objects.create(
            category=self.vehicles,
            subcategory=self.car,
            name="Old record",
            purchase_cost=Decimal("1000000.00"),
            location=self.location,
        )
        response = self.client.patch(
            f"/api/v1/assets/{asset.id}/", {"notes": "needs details"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["details"])
