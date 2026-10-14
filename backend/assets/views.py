from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from accounts.permissions import IsAdminOrSuperAdmin

from .models import Asset, Category, SubCategory
from .permissions import AdminReadSuperAdminWrite
from .serializers import AssetSerializer, CategorySerializer, SubCategorySerializer


class BaseRecordViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Create, list, view and edit. No delete: records are deactivated or disposed."""

    filter_backends = [SearchFilter, OrderingFilter]

    def filter_active(self, queryset):
        is_active = self.request.query_params.get("is_active")
        if is_active in ("true", "false"):
            queryset = queryset.filter(is_active=(is_active == "true"))
        return queryset


class CategoryViewSet(BaseRecordViewSet):
    permission_classes = [AdminReadSuperAdminWrite]
    serializer_class = CategorySerializer
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]

    def get_queryset(self):
        queryset = Category.objects.prefetch_related("subcategories__category")
        return self.filter_active(queryset)


class SubCategoryViewSet(BaseRecordViewSet):
    permission_classes = [AdminReadSuperAdminWrite]
    serializer_class = SubCategorySerializer
    search_fields = ["name", "category__name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        queryset = SubCategory.objects.select_related("category")
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)
        return self.filter_active(queryset)


class AssetViewSet(BaseRecordViewSet):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = AssetSerializer
    search_fields = ["asset_id", "name", "supplier", "invoice_number", "description"]
    ordering_fields = ["asset_id", "name", "purchase_date", "purchase_cost", "created_at"]

    def get_queryset(self):
        queryset = Asset.objects.select_related(
            "category", "subcategory", "location", "department", "created_by"
        )
        params = self.request.query_params
        for param, field in (
            ("category", "category_id"),
            ("subcategory", "subcategory_id"),
            ("location", "location_id"),
            ("department", "department_id"),
            ("status", "status"),
            ("condition", "condition"),
        ):
            if params.get(param):
                queryset = queryset.filter(**{field: params[param]})
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
