"""
Maps a sub-category's detail type to the serializer that handles that kind of
asset's extra fields. Each detail serializer is added here as its task is done.
(SIM cards and fuel cards are added in Tasks 5c and 5d.)
"""
from itdevices.serializers import ITDeviceDetailsSerializer
from vehicles.serializers import VehicleDetailsSerializer

from .models import DetailType

# detail type: (name of the reverse link on Asset, serializer class)
DETAIL_CONFIG = {
    DetailType.VEHICLE: ("vehicle_details", VehicleDetailsSerializer),
    DetailType.IT_DEVICE: ("it_device_details", ITDeviceDetailsSerializer),
}


def get_detail_config(subcategory):
    if subcategory is None:
        return None
    return DETAIL_CONFIG.get(subcategory.detail_type)
