from datetime import timedelta
from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Platform, ServiceType, Trip

MAX_RECEIPT_MB = 3
MAX_TRIP_AGE_DAYS = 365


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = (
            "platform", "service_type", "trip_date", "pickup_location", "dropoff_location",
            "distance_km", "gross_fare", "commission_deducted", "other_deductions", "tips",
            "net_received", "receipt_photo", "notes",
        )
        labels = {
            "gross_fare": "Gross fare (₱)",
            "commission_deducted": "Commission deducted (₱)",
            "other_deductions": "Other deductions (₱)",
            "tips": "Tips (₱)",
            "net_received": "Net amount received (₱)",
            "distance_km": "Distance (km)",
        }
        widgets = {
            "trip_date": forms.DateInput(attrs={"type": "date"}),
            "pickup_location": forms.TextInput(attrs={"placeholder": "e.g. SM City Cebu"}),
            "dropoff_location": forms.TextInput(attrs={"placeholder": "e.g. IT Park, Lahug"}),
            "gross_fare": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "0.00"}),
            "commission_deducted": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "0.00"}),
            "other_deductions": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "tips": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "net_received": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "0.00"}),
            "distance_km": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "receipt_photo": forms.FileInput(attrs={"accept": "image/*"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Anything unusual about this trip?"}),
        }
        help_texts = {"receipt_photo": "Optional. Screenshot or photo of the fare breakdown, up to 3 MB."}

    def __init__(self, *args, rider=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.rider = rider
        platforms = Platform.objects.filter(is_active=True)
        if self.instance.pk:
            platforms = platforms | Platform.objects.filter(pk=self.instance.platform_id)
        self.fields["platform"].queryset = platforms.distinct()
        self.fields["platform"].empty_label = "Select platform"
        if not self.instance.pk:
            self.initial.setdefault("trip_date", timezone.localdate())
            if rider is not None and rider.platforms:
                first = Platform.objects.filter(code=rider.platforms[0], is_active=True).first()
                if first:
                    self.initial.setdefault("platform", first.pk)

    # --- field rules -------------------------------------------------------

    def clean_trip_date(self):
        trip_date = self.cleaned_data["trip_date"]
        today = timezone.localdate()
        if trip_date > today:
            raise forms.ValidationError("Trip date cannot be in the future.")
        if trip_date < today - timedelta(days=MAX_TRIP_AGE_DAYS):
            raise forms.ValidationError("Trips older than one year cannot be logged.")
        return trip_date

    def clean_gross_fare(self):
        value = self.cleaned_data["gross_fare"]
        if value <= 0:
            raise forms.ValidationError("Gross fare must be greater than ₱0.00.")
        return value

    def _non_negative(self, name):
        value = self.cleaned_data.get(name)
        if value is None:
            return Decimal("0.00")
        if value < 0:
            raise forms.ValidationError("This amount cannot be negative.")
        return value

    def clean_commission_deducted(self):
        return self._non_negative("commission_deducted")

    def clean_other_deductions(self):
        return self._non_negative("other_deductions")

    def clean_tips(self):
        return self._non_negative("tips")

    def clean_net_received(self):
        return self._non_negative("net_received")

    def clean_distance_km(self):
        value = self.cleaned_data.get("distance_km")
        if value is not None and not (Decimal("0.1") <= value <= Decimal("500")):
            raise forms.ValidationError("Distance must be between 0.1 km and 500 km.")
        return value

    def clean_receipt_photo(self):
        photo = self.cleaned_data.get("receipt_photo")
        if photo and hasattr(photo, "size") and photo.size > MAX_RECEIPT_MB * 1024 * 1024:
            raise forms.ValidationError(f"Receipt photo must be {MAX_RECEIPT_MB} MB or smaller.")
        return photo

    # --- cross-field business rules -----------------------------------------

    def clean(self):
        cleaned = super().clean()
        gross = cleaned.get("gross_fare")
        commission = cleaned.get("commission_deducted")
        other = cleaned.get("other_deductions") or Decimal("0")
        tips = cleaned.get("tips") or Decimal("0")
        net = cleaned.get("net_received")
        pickup = (cleaned.get("pickup_location") or "").strip().lower()
        dropoff = (cleaned.get("dropoff_location") or "").strip().lower()

        if pickup and pickup == dropoff:
            self.add_error("dropoff_location", "Drop-off location must be different from the pickup location.")
        if gross is not None and commission is not None and commission > gross:
            self.add_error("commission_deducted", "Commission cannot be more than the gross fare.")
        if gross is not None and commission is not None and commission + other > gross + tips:
            self.add_error("other_deductions", "Total deductions cannot be more than the gross fare plus tips.")
        if gross is not None and net is not None and net > gross + tips:
            self.add_error("net_received", "Net received cannot be more than the gross fare plus tips.")
        return cleaned


class TripFilterForm(forms.Form):
    platform = forms.ModelChoiceField(queryset=Platform.objects.all(), required=False, empty_label="All platforms")
    service_type = forms.ChoiceField(choices=[("", "All services")] + list(ServiceType.choices), required=False)
    status = forms.ChoiceField(choices=[("", "Any fare status")] + list(Trip.CheckStatus.choices), required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def filter(self, queryset):
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data.get("platform"):
            queryset = queryset.filter(platform=data["platform"])
        if data.get("service_type"):
            queryset = queryset.filter(service_type=data["service_type"])
        if data.get("status"):
            queryset = queryset.filter(check_status=data["status"])
        if data.get("date_from"):
            queryset = queryset.filter(trip_date__gte=data["date_from"])
        if data.get("date_to"):
            queryset = queryset.filter(trip_date__lte=data["date_to"])
        return queryset
