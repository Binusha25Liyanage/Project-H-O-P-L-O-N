from rest_framework.test import APITestCase

from .models import Role, User

PASSWORD = "Str0ng-Pass-12345"


class AccountsApiTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            "super1", password=PASSWORD, role=Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            "admin1", password=PASSWORD, role=Role.ADMIN
        )
        self.user = User.objects.create_user(
            "user1", password=PASSWORD, role=Role.USER
        )

    def test_login_returns_tokens_and_role(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "admin1", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], Role.ADMIN)

    def test_unauthenticated_cannot_list_users(self):
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_current_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "user1")

    def test_normal_user_cannot_list_users(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 403)

    def test_admin_sees_only_normal_users(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 200)
        usernames = [u["username"] for u in response.data["results"]]
        self.assertEqual(usernames, ["user1"])

    def test_super_admin_sees_everyone(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.data["count"], 3)

    def test_admin_can_create_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/users/",
            {"username": "newuser", "password": PASSWORD, "role": Role.USER},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.get(username="newuser").must_change_password)

    def test_admin_cannot_create_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/users/",
            {"username": "sneaky", "password": PASSWORD, "role": Role.ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_super_admin_can_create_admin(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.post(
            "/api/v1/users/",
            {"username": "admin2", "password": PASSWORD, "role": Role.ADMIN},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_cannot_deactivate_own_account(self):
        self.client.force_authenticate(self.super_admin)
        response = self.client.patch(
            f"/api/v1/users/{self.super_admin.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/v1/auth/change-password/",
            {"old_password": PASSWORD, "new_password": "An0ther-Pass-67890"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("An0ther-Pass-67890"))
