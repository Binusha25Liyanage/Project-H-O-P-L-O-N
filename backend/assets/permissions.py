from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import Role


class AdminReadSuperAdminWrite(BasePermission):
    """Admins and Super Admins can read. Only Super Admins can change."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return user.role in (Role.ADMIN, Role.SUPER_ADMIN)
        return user.role == Role.SUPER_ADMIN
