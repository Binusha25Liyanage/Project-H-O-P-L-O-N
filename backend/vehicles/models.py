from django.db import models


class FuelType(models.TextChoices):
    PETROL = "PETROL", "Petrol"
    DIESEL = "DIESEL", "Diesel"
    HYBRID = "HYBRID", "Hybrid"
    ELECTRIC = "ELECTRIC", "Electric"
    OTHER = "OTHER", "Other"


class VehicleDetails(models.Model):
    """Extra fields for assets in the Vehicles category (cars, lorries, motorbikes)."""

    asset = models.OneToOneField(
        "assets.Asset", on_delete=models.CASCADE, related_name="vehicle_details"
    )
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    chassis_number = models.CharField(max_length=50, unique=True)
    engine_number = models.CharField(max_length=50, blank=True)
    fuel_type = models.CharField(
        max_length=20, choices=FuelType.choices, default=FuelType.PETROL
    )
    colour = models.CharField(max_length=50, blank=True)
    odometer_km = models.PositiveIntegerField(default=0)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    revenue_licence_expiry = models.DateField(null=True, blank=True)
    emission_test_expiry = models.DateField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "vehicle details"
        verbose_name_plural = "vehicle details"

    def __str__(self):
        return f"{self.registration_number} ({self.make} {self.model})"
