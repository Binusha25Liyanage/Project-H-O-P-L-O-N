"""
Maps a category code to the serializer that handles that category's extra
fields. Each detail serializer is added here as its task is completed.

Category codes must never change, so they are locked once created.
"""
from vehicles.serializers import VehicleDetailsSerializer

# category code: (name of the reverse link on Asset, serializer class)
DETAIL_CONFIG = {
    "VEH": ("vehicle_details", VehicleDetailsSerializer),
}


def get_detail_config(category):
    if category is None:
        return None
    return DETAIL_CONFIG.get(category.code)
