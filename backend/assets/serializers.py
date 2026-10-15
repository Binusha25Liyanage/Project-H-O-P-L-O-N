from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .details import get_detail_config
from .models import Asset, AssetStatus, Category, SubCategory

# Statuses an admin may set by hand. ASSIGNED is set by the assignment workflow
# (Task 7) and DISPOSED by the approval workflow (Task 12).
MANUAL_STATUSES = {AssetStatus.IN_STOCK, AssetStatus.UNDER_REPAIR, AssetStatus.LOST}


class _NoDeactivateWhileInUseMixin:
    """Block deactivating a category or sub-category that still has live assets."""

    def validate(self, attrs):
        if (
            self.instance
            and self.instance.is_active
            and attrs.get("is_active") is False
            and self.instance.assets.exclude(status=AssetStatus.DISPOSED).exists()
        ):
            raise serializers.ValidationError(
                "Cannot deactivate: assets that are not disposed still use this."
            )
        return attrs


class SubCategorySerializer(_NoDeactivateWhileInUseMixin, serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = SubCategory
        fields = ["id", "category", "category_name", "name", "is_active"]
        read_only_fields = ["id"]

    def validate_category(self, value):
        if self.instance and self.instance.category_id != value.pk:
            raise serializers.ValidationError(
                "A sub-category cannot be moved to another category."
            )
        if not value.is_active and not self.instance:
            raise serializers.ValidationError("This category is inactive.")
        return value


class CategorySerializer(_NoDeactivateWhileInUseMixin, serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "code", "is_active", "subcategories"]
        read_only_fields = ["id"]
        # Code uniqueness is checked by hand after tidying the text.
        extra_kwargs = {"code": {"validators": []}}

    def validate_code(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Code is required.")
        if self.instance and value != self.instance.code:
            raise serializers.ValidationError(
                "Category codes cannot be changed once created."
            )
        duplicates = Category.objects.filter(code=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A category with this code already exists.")
        return value


class AssetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    subcategory_name = serializers.CharField(source="subcategory.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    condition_display = serializers.CharField(
        source="get_condition_display", read_only=True
    )
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True, default=None
    )
    # Category-specific fields (vehicle, IT device, SIM, fuel card). Written here,
    # shown in the response by to_representation below.
    details = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Asset
        fields = [
            "id", "asset_id",
            "category", "category_name", "subcategory", "subcategory_name",
            "name", "description",
            "status", "status_display", "condition", "condition_display",
            "purchase_date", "purchase_cost", "current_value",
            "supplier", "invoice_number", "warranty_end_date",
            "location", "location_name", "department", "department_name",
            "notes", "details",
            "created_by", "created_by_username", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "asset_id", "current_value",
            "created_by", "created_at", "updated_at",
        ]

    def validate_details(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Details must be an object.")
        return value

    def validate_status(self, value):
        if self.instance and value == self.instance.status:
            return value
        if value not in MANUAL_STATUSES:
            raise serializers.ValidationError(
                f"Status '{value}' is set automatically by the system. "
                "You can set In stock, Under repair or Lost."
            )
        return value

    def validate_location(self, value):
        unchanged = self.instance and self.instance.location_id == value.pk
        if not value.is_active and not unchanged:
            raise serializers.ValidationError("This location is inactive.")
        return value

    def validate_department(self, value):
        unchanged = self.instance and self.instance.department_id == getattr(value, "pk", None)
        if value is not None and not value.is_active and not unchanged:
            raise serializers.ValidationError("This department is inactive.")
        return value

    def validate(self, attrs):
        instance = self.instance

        if instance:
            if instance.status == AssetStatus.DISPOSED:
                raise serializers.ValidationError("Disposed assets cannot be edited.")
            if (
                instance.status == AssetStatus.ASSIGNED
                and attrs.get("status", instance.status) != instance.status
            ):
                raise serializers.ValidationError(
                    "This asset is assigned. Return it before changing its status."
                )
            for field in ("category", "subcategory"):
                if field in attrs and attrs[field].pk != getattr(instance, f"{field}_id"):
                    raise serializers.ValidationError(
                        f"The {field} cannot be changed after the asset is created."
                    )

        category = attrs.get("category", instance.category if instance else None)
        subcategory = attrs.get("subcategory", instance.subcategory if instance else None)
        if category and subcategory and subcategory.category_id != category.pk:
            raise serializers.ValidationError(
                "The sub-category does not belong to the chosen category."
            )
        if not instance:
            if category and not category.is_active:
                raise serializers.ValidationError("This category is inactive.")
            if subcategory and not subcategory.is_active:
                raise serializers.ValidationError("This sub-category is inactive.")

        purchase_date = attrs.get(
            "purchase_date", instance.purchase_date if instance else None
        )
        warranty_end = attrs.get(
            "warranty_end_date", instance.warranty_end_date if instance else None
        )
        if purchase_date and purchase_date > timezone.localdate():
            raise serializers.ValidationError("The purchase date cannot be in the future.")
        if purchase_date and warranty_end and warranty_end < purchase_date:
            raise serializers.ValidationError(
                "The warranty end date cannot be before the purchase date."
            )
        return self._validate_details(attrs, category)

    def _validate_details(self, attrs, category):
        instance = self.instance
        details = attrs.pop("details", None)
        config = get_detail_config(category)

        if config is None:
            if details is not None:
                raise serializers.ValidationError(
                    {"details": "This category has no extra details yet."}
                )
            return attrs

        related_name, detail_class = config
        existing = getattr(instance, related_name, None) if instance else None
        if details is None:
            if not instance:
                raise serializers.ValidationError(
                    {"details": "Details are required for this category."}
                )
            return attrs

        detail_serializer = detail_class(
            instance=existing,
            data=details,
            partial=bool(self.partial and existing is not None),
            context=self.context,
        )
        try:
            detail_serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({"details": exc.detail})
        attrs["_detail_serializer"] = detail_serializer
        return attrs

    def create(self, validated_data):
        detail_serializer = validated_data.pop("_detail_serializer", None)
        with transaction.atomic():
            asset = super().create(validated_data)
            if detail_serializer:
                detail_serializer.save(asset=asset)
        return asset

    def update(self, instance, validated_data):
        detail_serializer = validated_data.pop("_detail_serializer", None)
        with transaction.atomic():
            asset = super().update(instance, validated_data)
            if detail_serializer:
                detail_serializer.save(asset=asset)
        return asset

    def to_representation(self, instance):
        data = super().to_representation(instance)
        details = None
        config = get_detail_config(instance.category)
        if config:
            related_name, detail_class = config
            detail_object = getattr(instance, related_name, None)
            if detail_object is not None:
                details = detail_class(detail_object, context=self.context).data
        data["details"] = details
        return data
