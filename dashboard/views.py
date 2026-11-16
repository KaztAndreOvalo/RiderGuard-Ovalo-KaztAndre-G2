from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import rider_required
from trips.models import Trip


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their role."""
    if request.user.is_admin_role:
        return redirect("adminpanel:dashboard")
    return redirect("dashboard:rider")


@rider_required
def rider_dashboard(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())  # Monday
    trips = Trip.objects.filter(rider=request.user)
    this_week = trips.filter(trip_date__gte=week_start)
    week_totals = this_week.aggregate(net=Sum("net_received"), gross=Sum("gross_fare"))

    stats = [
        {"label": "Earnings this week", "value": f"₱{week_totals['net'] or Decimal('0.00'):,.2f}",
         "note": f"Since {week_start:%b %d}"},
        {"label": "Trips this week", "value": this_week.count(), "note": f"{trips.count()} logged in total"},
        {"label": "Gross fares this week", "value": f"₱{week_totals['gross'] or Decimal('0.00'):,.2f}",
         "note": "Before commission"},
        {"label": "Pending disputes", "value": 0, "note": "Dispute Vault — Sprint 5"},
    ]
    return render(request, "dashboard/rider_dashboard.html", {
        "stats": stats,
        "recent_trips": trips.select_related("platform")[:5],
    })
