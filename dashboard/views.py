from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import rider_required


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their role."""
    if request.user.is_admin_role:
        return redirect("adminpanel:dashboard")
    return redirect("dashboard:rider")


@rider_required
def rider_dashboard(request):
    # Trip, fare and dispute data arrive in later sprints (Trip Logger, Fare Checker, Dispute Vault).
    stats = [
        {"label": "Earnings this week", "value": "₱0.00", "note": "Trip Logger — Sprint 3"},
        {"label": "Trips logged", "value": 0, "note": "Trip Logger — Sprint 3"},
        {"label": "Flagged fares", "value": 0, "note": "Fare Checker — Sprint 4"},
        {"label": "Pending disputes", "value": 0, "note": "Dispute Vault — Sprint 5"},
    ]
    return render(request, "dashboard/rider_dashboard.html", {"stats": stats})
