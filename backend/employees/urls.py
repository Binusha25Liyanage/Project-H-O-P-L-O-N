from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import DepartmentViewSet, EmployeeViewSet, LocationViewSet

router = SimpleRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("locations", LocationViewSet, basename="location")
router.register("employees", EmployeeViewSet, basename="employee")

urlpatterns = [
    path("", include(router.urls)),
]
