from django.db import models


class ConnectionType(models.TextChoices):
    NONE = "", "Not applicable"
    USB = "USB", "USB"
    NETWORK = "NETWORK", "Network (LAN)"
    WIFI = "WIFI", "Wi-Fi"
    BLUETOOTH = "BLUETOOTH", "Bluetooth"
    OTHER = "OTHER", "Other"


class ITDeviceDetails(models.Model):
    """
    Extra fields for IT devices: laptops, smartphones, mobile phones, landlines,
    printers and thermal printers. (SIM cards have their own details, Task 5c.)
    """

    asset = models.OneToOneField(
        "assets.Asset", on_delete=models.CASCADE, related_name="it_device_details"
    )
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    # Optional but unique when present. Empty is stored as NULL so that several
    # devices without a serial number do not clash with each other.
    serial_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    imei = models.CharField(max_length=15, unique=True, null=True, blank=True)
    imei_2 = models.CharField(
        max_length=15, unique=True, null=True, blank=True,
        help_text="Second IMEI for dual-SIM phones.",
    )
    processor = models.CharField(max_length=100, blank=True)
    ram_gb = models.PositiveSmallIntegerField(null=True, blank=True)
    storage_gb = models.PositiveIntegerField(null=True, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    connection_type = models.CharField(
        max_length=20, choices=ConnectionType.choices, blank=True, default=""
    )
    landline_number = models.CharField(max_length=30, blank=True)
    extension = models.CharField(max_length=20, blank=True)
    accessories = models.TextField(
        blank=True, help_text="Charger, bag, mouse, cables and so on."
    )

    class Meta:
        verbose_name = "IT device details"
        verbose_name_plural = "IT device details"

    def __str__(self):
        return f"{self.brand} {self.model}"
