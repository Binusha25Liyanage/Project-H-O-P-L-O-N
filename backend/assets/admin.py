from django.contrib import admin

from .models import Asset, Category, SubCategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "detail_type", "is_active")
    list_filter = ("category", "is_active")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "asset_id", "name", "category", "subcategory", "status", "condition", "location",
    )
    list_filter = ("category", "status", "condition", "location")
    search_fields = ("asset_id", "name", "supplier", "invoice_number")
    readonly_fields = ("asset_id",)
