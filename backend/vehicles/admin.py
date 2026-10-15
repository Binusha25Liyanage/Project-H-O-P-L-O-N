from django.contrib import admin

from .models import VehicleDetails


@admin.register(VehicleDetails)
class VehicleDetailsAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "make", "model", "year", "asset")
    search_fields = ("registration_number", "chassis_number", "make", "model")
