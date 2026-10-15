from django.db.models import Q
from rest_framework import serializers

from .models import ITDeviceDetails


def _luhn_ok(digits):
    """The check-digit test every real IMEI passes."""
    total = 0
    for position, char in enumerate(reversed(digits)):
        number = int(char)
        if position % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


class ITDeviceDetailsSerializer(serializers.ModelSerializer):
    """The `details` block of an IT device asset. The asset link is set by the asset."""

    class Meta:
        model = ITDeviceDetails
        fields = [
            "brand", "model", "serial_number", "imei", "imei_2",
            "processor", "ram_gb", "storage_gb", "operating_system",
            "connection_type", "landline_number", "extension", "accessories",
        ]
        # Uniqueness is checked by hand after the text is tidied. The IMEI fields
        # allow extra length on input so spaces and dashes (49-015420 323751-8)
        # can be typed; they are removed before the 15-digit check below.
        extra_kwargs = {
            "serial_number": {"validators": []},
            "imei": {"validators": [], "max_length": 30},
            "imei_2": {"validators": [], "max_length": 30},
        }

    def validate_brand(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Brand is required.")
        return value

    def validate_model(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Model is required.")
        return value

    def validate_serial_number(self, value):
        value = " ".join((value or "").upper().split())
        if not value:
            return None
        duplicates = ITDeviceDetails.objects.filter(serial_number=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                "A device with this serial number already exists."
            )
        return value

    def _clean_imei(self, value):
        value = (value or "").replace(" ", "").replace("-", "")
        if not value:
            return None
        if not (value.isdigit() and len(value) == 15):
            raise serializers.ValidationError("An IMEI is exactly 15 digits.")
        if not _luhn_ok(value):
            raise serializers.ValidationError(
                "This IMEI is not valid. Please check the number."
            )
        duplicates = ITDeviceDetails.objects.filter(Q(imei=value) | Q(imei_2=value))
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A device with this IMEI already exists.")
        return value

    def validate_imei(self, value):
        return self._clean_imei(value)

    def validate_imei_2(self, value):
        return self._clean_imei(value)

    def validate_extension(self, value):
        return value.strip()

    def validate(self, attrs):
        imei = attrs.get("imei", self.instance.imei if self.instance else None)
        imei_2 = attrs.get("imei_2", self.instance.imei_2 if self.instance else None)
        if imei and imei_2 and imei == imei_2:
            raise serializers.ValidationError("IMEI and second IMEI must be different.")
        return attrs
