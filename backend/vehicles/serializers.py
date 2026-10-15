from django.utils import timezone
from rest_framework import serializers

from .models import VehicleDetails


def _tidy(value):
    """Capitals, single spaces, no padding: 'wp  cab-1234 ' becomes 'WP CAB-1234'."""
    return " ".join(value.upper().split())


class VehicleDetailsSerializer(serializers.ModelSerializer):
    """The `details` block of a Vehicles asset. The asset link is set by the asset."""

    class Meta:
        model = VehicleDetails
        fields = [
            "registration_number", "make", "model", "year",
            "chassis_number", "engine_number", "fuel_type", "colour",
            "odometer_km",
            "insurance_provider", "insurance_expiry",
            "revenue_licence_expiry", "emission_test_expiry", "next_service_date",
        ]
        # Uniqueness is checked by hand after the text is tidied (see _check_unique).
        extra_kwargs = {
            "registration_number": {"validators": []},
            "chassis_number": {"validators": []},
        }

    def _check_unique(self, field, value, label):
        duplicates = VehicleDetails.objects.filter(**{field: value})
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                f"A vehicle with this {label} already exists."
            )

    def validate_registration_number(self, value):
        value = _tidy(value)
        if not value:
            raise serializers.ValidationError("Registration number is required.")
        self._check_unique("registration_number", value, "registration number")
        return value

    def validate_chassis_number(self, value):
        value = _tidy(value)
        if not value:
            raise serializers.ValidationError("Chassis number is required.")
        self._check_unique("chassis_number", value, "chassis number")
        return value

    def validate_engine_number(self, value):
        return _tidy(value)

    def validate_year(self, value):
        latest = timezone.localdate().year + 1
        if value < 1950 or value > latest:
            raise serializers.ValidationError(f"Year must be between 1950 and {latest}.")
        return value

    def validate_odometer_km(self, value):
        if self.instance and value < self.instance.odometer_km:
            raise serializers.ValidationError(
                "The odometer reading cannot be lower than the recorded "
                f"{self.instance.odometer_km} km."
            )
        return value
