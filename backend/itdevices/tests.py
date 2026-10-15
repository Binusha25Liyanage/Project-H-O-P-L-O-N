from rest_framework.test import APITestCase

from accounts.models import Role, User
from assets.models import Asset, Category, DetailType, SubCategory
from employees.models import Location

from .models import ITDeviceDetails

PASSWORD = "Str0ng-Pass-12345"
IMEI_A = "490154203237518"
IMEI_B = "356938035643809"


class ITDeviceDetailsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "admin1", password=PASSWORD, role=Role.ADMIN
        )
        self.location = Location.objects.create(name="Head Office")
        self.it = Category.objects.create(name="IT Equipment", code="ITE")
        self.laptop = SubCategory.objects.create(
            category=self.it, name="Laptop", detail_type=DetailType.IT_DEVICE
        )
        self.phone = SubCategory.objects.create(
            category=self.it, name="Smartphone", detail_type=DetailType.IT_DEVICE
        )
        self.sim = SubCategory.objects.create(
            category=self.it, name="SIM Card", detail_type=DetailType.SIM
        )
        self.client.force_authenticate(self.admin)

    def details(self, **overrides):
        data = {
            "brand": "Dell",
            "model": "Latitude 5440",
            "serial_number": "abc123",
            "processor": "Intel i7",
            "ram_gb": 16,
            "storage_gb": 512,
            "operating_system": "Windows 11 Pro",
            "accessories": "Charger, laptop bag",
        }
        data.update(overrides)
        return data

    def payload(self, subcategory=None, **overrides):
        data = {
            "category": self.it.id,
            "subcategory": (subcategory or self.laptop).id,
            "name": "Dell laptop",
            "purchase_cost": "250000.00",
            "location": self.location.id,
            "details": self.details(),
        }
        data.update(overrides)
        return data

    def post(self, payload):
        return self.client.post("/api/v1/assets/", payload, format="json")

    def test_create_laptop_with_details(self):
        response = self.post(self.payload())
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["details"]["brand"], "Dell")
        self.assertEqual(response.data["details"]["serial_number"], "ABC123")
        self.assertEqual(response.data["details"]["ram_gb"], 16)
        self.assertEqual(ITDeviceDetails.objects.count(), 1)

    def test_details_required_for_it_device(self):
        payload = self.payload()
        del payload["details"]
        response = self.post(payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("details", response.data)

    def test_missing_brand_rejected_and_no_asset_left_behind(self):
        details = self.details()
        del details["brand"]
        response = self.post(self.payload(details=details))
        self.assertEqual(response.status_code, 400)
        self.assertIn("brand", response.data["details"])
        self.assertEqual(Asset.objects.count(), 0)

    def test_duplicate_serial_number_rejected_in_any_case(self):
        self.assertEqual(self.post(self.payload()).status_code, 201)
        response = self.post(self.payload(details=self.details(serial_number="ABC123")))
        self.assertEqual(response.status_code, 400)
        self.assertIn("serial_number", response.data["details"])
        self.assertEqual(Asset.objects.count(), 1)

    def test_devices_without_serial_number_do_not_clash(self):
        first = self.post(self.payload(details=self.details(serial_number="")))
        second = self.post(self.payload(details=self.details(serial_number="")))
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)
        self.assertIsNone(first.data["details"]["serial_number"])

    def test_phone_with_valid_imei(self):
        response = self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(brand="Samsung", model="S24", imei=IMEI_A),
            )
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["details"]["imei"], IMEI_A)

    def test_imei_with_dashes_and_spaces_is_cleaned(self):
        response = self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(imei="49-015420 323751-8"),
            )
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["details"]["imei"], IMEI_A)

    def test_imei_wrong_length_rejected(self):
        response = self.post(
            self.payload(subcategory=self.phone, details=self.details(imei="12345"))
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("imei", response.data["details"])

    def test_imei_failing_check_digit_rejected(self):
        response = self.post(
            self.payload(
                subcategory=self.phone, details=self.details(imei="490154203237519")
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("imei", response.data["details"])

    def test_duplicate_imei_rejected(self):
        self.post(self.payload(subcategory=self.phone, details=self.details(imei=IMEI_A)))
        response = self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(serial_number="zzz", imei=IMEI_A),
            )
        )
        self.assertEqual(response.status_code, 400)

    def test_imei_matching_another_devices_second_imei_rejected(self):
        self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(imei=IMEI_A, imei_2=IMEI_B),
            )
        )
        response = self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(serial_number="zzz", imei=IMEI_B),
            )
        )
        self.assertEqual(response.status_code, 400)

    def test_imei_and_second_imei_must_differ(self):
        response = self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(imei=IMEI_A, imei_2=IMEI_A),
            )
        )
        self.assertEqual(response.status_code, 400)

    def test_sim_subcategory_has_no_details_yet(self):
        no_details = self.payload(subcategory=self.sim, name="SIM")
        del no_details["details"]
        self.assertEqual(self.post(no_details).status_code, 201)
        with_details = self.payload(subcategory=self.sim, name="SIM 2")
        self.assertEqual(self.post(with_details).status_code, 400)

    def test_patch_details_partially(self):
        created = self.post(self.payload()).data
        response = self.client.patch(
            f"/api/v1/assets/{created['id']}/",
            {"details": {"ram_gb": 32, "accessories": "Charger"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["details"]["ram_gb"], 32)
        self.assertEqual(response.data["details"]["brand"], "Dell")

    def test_own_serial_number_can_be_resubmitted_on_update(self):
        created = self.post(self.payload()).data
        response = self.client.patch(
            f"/api/v1/assets/{created['id']}/",
            {"details": {"serial_number": "abc123"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_retrieve_includes_details_and_search_by_serial_and_imei(self):
        created = self.post(
            self.payload(
                subcategory=self.phone,
                details=self.details(serial_number="sn-777", imei=IMEI_A),
            )
        ).data
        one = self.client.get(f"/api/v1/assets/{created['id']}/")
        self.assertEqual(one.data["details"]["brand"], "Dell")
        by_serial = self.client.get("/api/v1/assets/?search=SN-777")
        self.assertEqual(by_serial.data["count"], 1)
        by_imei = self.client.get(f"/api/v1/assets/?search={IMEI_A}")
        self.assertEqual(by_imei.data["count"], 1)
