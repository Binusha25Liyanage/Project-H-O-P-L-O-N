from rest_framework.test import APITestCase

from accounts.models import Role, User

from .models import Department, Employee, Location

PASSWORD = "Str0ng-Pass-12345"


class EmployeesApiTests(APITestCase):
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
        self.department = Department.objects.create(name="Sales")
        self.location = Location.objects.create(name="Head Office")

    def employee_payload(self, **overrides):
        payload = {
            "employee_number": "emp-001",
            "first_name": "Nimal",
            "last_name": "Perera",
            "designation": "Sales Executive",
            "department": self.department.id,
            "location": self.location.id,
        }
        payload.update(overrides)
        return payload

    def make_employee(self, **overrides):
        data = {
            "employee_number": "EMP-100",
            "first_name": "Kamal",
            "last_name": "Silva",
            "department": self.department,
            "location": self.location,
        }
        data.update(overrides)
        return Employee.objects.create(**data)

    # Departments and locations
    def test_admin_can_create_department(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/departments/", {"name": "Finance"}, format="json"
        )
        self.assertEqual(response.status_code, 201)

    def test_normal_user_cannot_create_department(self):
        self.client.force_authenticate(self.normal_user)
        response = self.client.post(
            "/api/v1/departments/", {"name": "Finance"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_duplicate_department_name_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/departments/", {"name": "Sales"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_deactivate_department_with_active_employees(self):
        self.make_employee()
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/departments/{self.department.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_can_deactivate_empty_location(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/v1/locations/{self.location.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    # Employees
    def test_admin_can_create_employee_and_number_is_normalised(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/employees/", self.employee_payload(), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["employee_number"], "EMP-001")
        self.assertEqual(response.data["full_name"], "Nimal Perera")
        self.assertEqual(response.data["department_name"], "Sales")

    def test_duplicate_employee_number_rejected(self):
        self.make_employee(employee_number="EMP-001")
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/employees/", self.employee_payload(), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_normal_user_cannot_list_employees(self):
        self.client.force_authenticate(self.normal_user)
        response = self.client.get("/api/v1/employees/")
        self.assertEqual(response.status_code, 403)

    def test_inactive_department_cannot_be_used_for_new_employee(self):
        self.department.is_active = False
        self.department.save()
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/employees/", self.employee_payload(), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_cannot_link_admin_account(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            self.employee_payload(user=self.super_admin.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_account_cannot_link_to_two_employees(self):
        self.make_employee(user=self.normal_user)
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            self.employee_payload(user=self.normal_user.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_search_employees_by_name(self):
        self.make_employee(employee_number="EMP-100", first_name="Kamal")
        self.make_employee(employee_number="EMP-101", first_name="Sunil")
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/employees/?search=Sunil")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["employee_number"], "EMP-101")

    def test_me_returns_linked_employee(self):
        self.make_employee(user=self.normal_user)
        self.client.force_authenticate(self.normal_user)
        response = self.client.get("/api/v1/employees/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["employee_number"], "EMP-100")

    def test_me_without_employee_record_is_404(self):
        self.client.force_authenticate(self.normal_user)
        response = self.client.get("/api/v1/employees/me/")
        self.assertEqual(response.status_code, 404)
