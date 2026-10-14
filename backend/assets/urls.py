from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AssetViewSet, CategoryViewSet, SubCategoryViewSet

router = SimpleRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("subcategories", SubCategoryViewSet, basename="subcategory")
router.register("assets", AssetViewSet, basename="asset")

urlpatterns = [
    path("", include(router.urls)),
]
