from django.db.models import Count, Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminOrSuperAdmin

from .models import Department, Employee, Location
from .serializers import DepartmentSerializer, EmployeeSerializer, LocationSerializer


class BaseRecordViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Create, list, view and edit. No delete: records are deactivated
    (is_active=false) so history stays intact.
    """

    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [SearchFilter, OrderingFilter]

    def filter_active(self, queryset):
        is_active = self.request.query_params.get("is_active")
        if is_active in ("true", "false"):
            queryset = queryset.filter(is_active=(is_active == "true"))
        return queryset


class DepartmentViewSet(BaseRecordViewSet):
    serializer_class = DepartmentSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        queryset = Department.objects.annotate(
            active_employee_count=Count(
                "employees", filter=Q(employees__is_active=True)
            )
        )
        return self.filter_active(queryset)


class LocationViewSet(BaseRecordViewSet):
    serializer_class = LocationSerializer
    search_fields = ["name", "address"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        queryset = Location.objects.annotate(
            active_employee_count=Count(
                "employees", filter=Q(employees__is_active=True)
            )
        )
        return self.filter_active(queryset)


class EmployeeViewSet(BaseRecordViewSet):
    serializer_class = EmployeeSerializer
    search_fields = [
        "employee_number", "first_name", "last_name", "email", "phone", "designation",
    ]
    ordering_fields = ["employee_number", "first_name", "created_at"]

    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = Employee.objects.select_related("department", "location", "user")
        params = self.request.query_params
        if params.get("department"):
            queryset = queryset.filter(department_id=params["department"])
        if params.get("location"):
            queryset = queryset.filter(location_id=params["location"])
        return self.filter_active(queryset)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """The employee record linked to the logged-in account."""
        employee = (
            Employee.objects.select_related("department", "location", "user")
            .filter(user=request.user)
            .first()
        )
        if employee is None:
            return Response(
                {"detail": "No employee record is linked to this account."},
                status=404,
            )
        return Response(self.get_serializer(employee).data)
