from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin"
    USER = "USER", "User"


class User(AbstractUser):
    """Login account for Hoplon. Employee details are linked in Task 3."""

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    phone = models.CharField(max_length=30, blank=True)
    must_change_password = models.BooleanField(default=False)

    class Meta:
        ordering = ["username"]

    def save(self, *args, **kwargs):
        # Accounts made with `createsuperuser` are always Super Admins.
        if self.is_superuser:
            self.role = Role.SUPER_ADMIN
        super().save(*args, **kwargs)

    @property
    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    @property
    def is_admin_level(self):
        return self.role in (Role.SUPER_ADMIN, Role.ADMIN)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
