from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ServiceType(models.TextChoices):
    RIDE = "RIDE", "Ride-hailing"
    DELIVERY = "DELIVERY", "Parcel delivery"
    FOOD = "FOOD", "Food delivery"


class Platform(models.Model):
    """A ride-hailing / delivery platform such as Maxim, MoveIt or Grab."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=60, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CommissionRate(models.Model):
    """Reference commission rate for a platform and service, used by the Fare Checker."""

    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="commission_rates")
    service_type = models.CharField(max_length=10, choices=ServiceType.choices)
    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="Percentage of the gross fare the platform keeps.",
    )
    effective_from = models.DateField(help_text="Date this rate started applying.")
    source_note = models.CharField(
        max_length=200, blank=True,
        help_text="Where this rate comes from (e.g. platform announcement, LTFRB memo).",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="commission_rates_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["platform__name", "service_type", "-effective_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "service_type", "effective_from"],
                name="unique_rate_per_platform_service_date",
            )
        ]

    def __str__(self):
        return f"{self.platform} {self.get_service_type_display()} {self.commission_percent}% (from {self.effective_from})"


class Trip(models.Model):
    """One trip or delivery logged by a rider, with its fare breakdown."""

    rider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trips")
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT, related_name="trips")
    service_type = models.CharField(max_length=10, choices=ServiceType.choices, default=ServiceType.RIDE)
    trip_date = models.DateField()
    pickup_location = models.CharField(max_length=120)
    dropoff_location = models.CharField(max_length=120)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    gross_fare = models.DecimalField(
        max_digits=9, decimal_places=2, help_text="Total fare the passenger/customer paid."
    )
    commission_deducted = models.DecimalField(
        max_digits=9, decimal_places=2, help_text="Commission the platform deducted, as shown on your breakdown."
    )
    other_deductions = models.DecimalField(
        max_digits=9, decimal_places=2, default=Decimal("0.00"),
        help_text="Other fees deducted (booking fee, insurance, etc.).",
    )
    tips = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
    net_received = models.DecimalField(
        max_digits=9, decimal_places=2, help_text="Amount actually credited to you for this trip."
    )

    receipt_photo = models.ImageField(upload_to="trip_receipts/%Y/%m/", blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-trip_date", "-created_at"]
        indexes = [models.Index(fields=["rider", "-trip_date"])]

    def __str__(self):
        return f"{self.platform} trip on {self.trip_date} ({self.rider})"

    @property
    def total_deductions(self):
        return self.commission_deducted + self.other_deductions

    @property
    def commission_percent_charged(self):
        if not self.gross_fare:
            return Decimal("0")
        return (self.commission_deducted / self.gross_fare * 100).quantize(Decimal("0.01"))
