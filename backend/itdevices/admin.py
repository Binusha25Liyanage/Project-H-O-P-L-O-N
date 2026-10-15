from django.contrib import admin

from .models import ITDeviceDetails


@admin.register(ITDeviceDetails)
class ITDeviceDetailsAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "serial_number", "imei", "asset")
    search_fields = ("brand", "model", "serial_number", "imei", "imei_2")
