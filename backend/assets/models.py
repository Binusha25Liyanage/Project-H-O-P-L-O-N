from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction


class Category(models.Model):
    """Top-level asset group: Vehicles, IT Equipment, Fuel Cards."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """Car, Lorry, Laptop, Printer, SIM Card, and so on."""

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="subcategories"
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category__name", "name"]
        verbose_name_plural = "sub-categories"
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_subcategory_per_category"
            )
        ]

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class AssetStatus(models.TextChoices):
    IN_STOCK = "IN_STOCK", "In stock"
    ASSIGNED = "ASSIGNED", "Assigned"
    UNDER_REPAIR = "UNDER_REPAIR", "Under repair"
    LOST = "LOST", "Lost"
    DISPOSED = "DISPOSED", "Disposed"


class AssetCondition(models.TextChoices):
    NEW = "NEW", "New"
    GOOD = "GOOD", "Good"
    FAIR = "FAIR", "Fair"
    POOR = "POOR", "Poor"
    DAMAGED = "DAMAGED", "Damaged"


class Asset(models.Model):
    """
    The shared record for every company asset. Category-specific details
    (vehicle, IT device, SIM, fuel card) are added in Task 5.

    Assets are never deleted. They end their life as Disposed.
    """

    asset_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True, editable=False
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="assets"
    )
    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.PROTECT, related_name="assets"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20, choices=AssetStatus.choices, default=AssetStatus.IN_STOCK
    )
    condition = models.CharField(
        max_length=20, choices=AssetCondition.choices, default=AssetCondition.NEW
    )

    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    current_value = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Starts equal to the purchase cost. Depreciation updates it (Task 10).",
    )
    supplier = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    warranty_end_date = models.DateField(null=True, blank=True)

    location = models.ForeignKey(
        "employees.Location", on_delete=models.PROTECT, related_name="assets"
    )
    department = models.ForeignKey(
        "employees.Department",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assets",
    )
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating and self.current_value is None:
            self.current_value = self.purchase_cost
        with transaction.atomic():
            super().save(*args, **kwargs)
            if creating and not self.asset_id:
                self.asset_id = f"AST-{self.pk:06d}"
                super().save(update_fields=["asset_id"])

    def __str__(self):
        return f"{self.asset_id} - {self.name}"
