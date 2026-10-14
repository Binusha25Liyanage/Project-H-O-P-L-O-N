from rest_framework import serializers

from accounts.models import Role

from .models import Department, Employee, Location


class _NoDeactivateWhileInUseMixin:
    """Block deactivating a department or location that still has staff."""

    def validate(self, attrs):
        if (
            self.instance
            and self.instance.is_active
            and attrs.get("is_active") is False
            and self.instance.employees.filter(is_active=True).exists()
        ):
            raise serializers.ValidationError(
                "Cannot deactivate: active employees still belong here. "
                "Move or deactivate them first."
            )
        return attrs


class DepartmentSerializer(_NoDeactivateWhileInUseMixin, serializers.ModelSerializer):
    active_employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "is_active", "active_employee_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_active_employee_count(self, obj):
        value = getattr(obj, "active_employee_count", None)
        if value is not None:
            return value
        return obj.employees.filter(is_active=True).count()


class LocationSerializer(_NoDeactivateWhileInUseMixin, serializers.ModelSerializer):
    active_employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id", "name", "address", "is_active",
            "active_employee_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_active_employee_count(self, obj):
        value = getattr(obj, "active_employee_count", None)
        if value is not None:
            return value
        return obj.employees.filter(is_active=True).count()


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id", "employee_number", "first_name", "last_name", "full_name",
            "email", "phone", "designation",
            "department", "department_name",
            "location", "location_name",
            "user", "username",
            "date_joined", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        # The uniqueness check is done by hand below, after the number has been
        # tidied up. The automatic check would compare the raw text ("emp-001")
        # before it becomes "EMP-001" and miss duplicates.
        extra_kwargs = {"employee_number": {"validators": []}}

    def validate_employee_number(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Employee number is required.")
        duplicates = Employee.objects.filter(employee_number=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                "An employee with this number already exists."
            )
        return value

    def _check_active(self, value, current, label):
        """A new or changed choice must be active; an unchanged one is left alone."""
        unchanged = current is not None and current.pk == value.pk
        if not value.is_active and not unchanged:
            raise serializers.ValidationError(f"This {label} is inactive.")
        return value

    def validate_department(self, value):
        current = self.instance.department if self.instance else None
        return self._check_active(value, current, "department")

    def validate_location(self, value):
        current = self.instance.location if self.instance else None
        return self._check_active(value, current, "location")

    def validate_user(self, value):
        request_user = self.context["request"].user
        if value is not None and request_user.role == Role.ADMIN and value.role != Role.USER:
            raise serializers.ValidationError(
                "Admins can only link accounts with the User role."
            )
        return value
