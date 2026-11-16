"""Admin-only screens for the Fare Checker: reference commission rates and a read-only view of all trips."""

from datetime import timedelta

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import admin_required
from trips.fare_check import recheck_trips
from trips.forms import TripFilterForm
from trips.models import CommissionRate, Platform, Trip


class CommissionRateForm(forms.ModelForm):
    class Meta:
        model = CommissionRate
        fields = ("platform", "service_type", "commission_percent", "effective_from", "source_note")
        labels = {"commission_percent": "Commission (%)"}
        widgets = {
            "effective_from": forms.DateInput(attrs={"type": "date"}),
            "commission_percent": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100"}),
            "source_note": forms.TextInput(attrs={"placeholder": "e.g. Platform announcement, March 2026"}),
        }

    def clean_effective_from(self):
        value = self.cleaned_data["effective_from"]
        if value > timezone.localdate() + timedelta(days=365):
            raise forms.ValidationError("Effective date cannot be more than a year ahead.")
        return value

    def clean(self):
        cleaned = super().clean()
        platform, service, date = cleaned.get("platform"), cleaned.get("service_type"), cleaned.get("effective_from")
        if platform and service and date:
            clash = CommissionRate.objects.filter(platform=platform, service_type=service, effective_from=date)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError(
                    "A rate for this platform and service already starts on that date. Edit that rate instead."
                )
        return cleaned


def _recheck(request, *pairs):
    total = sum(recheck_trips(p, s) for p, s in set(pairs))
    if total:
        messages.info(request, f"Re-checked {total} logged trip{'s' if total != 1 else ''} against the updated rates.")


@admin_required
def rate_list(request):
    rates = CommissionRate.objects.select_related("platform", "created_by")
    platform_id = request.GET.get("platform", "")
    if platform_id.isdigit():
        rates = rates.filter(platform_id=platform_id)
    return render(request, "adminpanel/rate_list.html", {
        "rates": rates, "platforms": Platform.objects.all(), "platform_id": platform_id,
    })


@admin_required
def rate_create(request):
    form = CommissionRateForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            rate = form.save(commit=False)
            rate.created_by = request.user
            rate.save()
            messages.success(request, f"Reference rate added: {rate}.")
            _recheck(request, (rate.platform, rate.service_type))
            return redirect("adminpanel:rates")
        messages.error(request, "Please correct the errors below.")
    return render(request, "adminpanel/rate_form.html", {"form": form, "title": "Add reference rate"})


@admin_required
def rate_edit(request, pk):
    rate = get_object_or_404(CommissionRate, pk=pk)
    before = (rate.platform, rate.service_type)
    form = CommissionRateForm(request.POST or None, instance=rate)
    if request.method == "POST":
        if form.is_valid():
            rate = form.save()
            messages.success(request, f"Reference rate updated: {rate}.")
            _recheck(request, before, (rate.platform, rate.service_type))
            return redirect("adminpanel:rates")
        messages.error(request, "Please correct the errors below.")
    return render(request, "adminpanel/rate_form.html", {"form": form, "rate": rate, "title": "Edit reference rate"})


@admin_required
def rate_delete(request, pk):
    rate = get_object_or_404(CommissionRate, pk=pk)
    if request.method == "POST":
        pair = (rate.platform, rate.service_type)
        label = str(rate)
        rate.delete()
        messages.success(request, f"Reference rate deleted: {label}.")
        _recheck(request, pair)
        return redirect("adminpanel:rates")
    return render(request, "adminpanel/rate_confirm_delete.html", {
        "rate": rate, "trip_count": rate.checked_trips.count(),
    })


@admin_required
def all_trips(request):
    """Admins can read every rider's trips (to spot platform-wide issues) but not change them."""
    trips = Trip.objects.select_related("platform", "rider")
    filter_form = TripFilterForm(request.GET or None)
    trips = filter_form.filter(trips)
    q = request.GET.get("q", "").strip()
    if q:
        trips = trips.filter(
            Q(rider__username__icontains=q) | Q(rider__first_name__icontains=q) | Q(rider__last_name__icontains=q)
        )
    page = Paginator(trips, 15).get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)
    return render(request, "adminpanel/trip_list.html", {
        "page": page, "filter_form": filter_form, "q": q, "querystring": querystring.urlencode(),
    })


@admin_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip.objects.select_related("platform", "rider", "applied_rate"), pk=pk)
    return render(request, "adminpanel/trip_detail.html", {"trip": trip})
