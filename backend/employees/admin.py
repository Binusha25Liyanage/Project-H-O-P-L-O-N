from django.contrib import admin

from .models import Department, Employee, Location


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number", "first_name", "last_name",
        "department", "location", "is_active",
    )
    list_filter = ("is_active", "department", "location")
    search_fields = ("employee_number", "first_name", "last_name", "email")
