from rest_framework.permissions import BasePermission

from .models import Role


class IsSuperAdmin(BasePermission):
    """Managing Director / IT Manager only."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == Role.SUPER_ADMIN)


class IsAdminOrSuperAdmin(BasePermission):
    """IT Officers and above."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in (Role.ADMIN, Role.SUPER_ADMIN)
        )
