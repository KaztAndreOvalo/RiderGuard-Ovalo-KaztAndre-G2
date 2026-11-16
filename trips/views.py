from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import rider_required

from .forms import TripFilterForm, TripForm
from .models import Trip


def _own_trip(request, pk):
    """A rider can only ever load their own trips; anyone else's id returns 404."""
    return get_object_or_404(Trip.objects.select_related("platform"), pk=pk, rider=request.user)


@rider_required
def trip_list(request):
    trips = Trip.objects.filter(rider=request.user).select_related("platform")
    filter_form = TripFilterForm(request.GET or None)
    trips = filter_form.filter(trips)
    page = Paginator(trips, 10).get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)
    return render(request, "trips/trip_list.html", {
        "page": page, "filter_form": filter_form, "querystring": querystring.urlencode(),
    })


@rider_required
def trip_create(request):
    form = TripForm(request.POST or None, request.FILES or None, rider=request.user)
    if request.method == "POST":
        if form.is_valid():
            trip = form.save(commit=False)
            trip.rider = request.user
            trip.save()
            messages.success(request, "Trip logged successfully.")
            return redirect("trips:detail", pk=trip.pk)
        messages.error(request, "Please correct the errors below.")
    return render(request, "trips/trip_form.html", {"form": form, "title": "Log a trip"})


@rider_required
def trip_detail(request, pk):
    trip = _own_trip(request, pk)
    return render(request, "trips/trip_detail.html", {"trip": trip})


@rider_required
def trip_edit(request, pk):
    trip = _own_trip(request, pk)
    form = TripForm(request.POST or None, request.FILES or None, instance=trip, rider=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Trip updated.")
            return redirect("trips:detail", pk=trip.pk)
        messages.error(request, "Please correct the errors below.")
    return render(request, "trips/trip_form.html", {"form": form, "trip": trip, "title": "Edit trip"})


@rider_required
def trip_delete(request, pk):
    trip = _own_trip(request, pk)
    if request.method == "POST":
        if trip.receipt_photo:
            trip.receipt_photo.delete(save=False)
        trip.delete()
        messages.success(request, "Trip deleted.")
        return redirect("trips:list")
    return render(request, "trips/trip_confirm_delete.html", {"trip": trip})
