from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import admin_required
from accounts.models import User


@admin_required
def admin_dashboard(request):
    week_ago = timezone.now() - timedelta(days=7)
    users = User.objects.all()
    context = {
        "total_users": users.count(),
        "total_riders": users.filter(role=User.Role.RIDER).count(),
        "total_admins": users.filter(role=User.Role.ADMIN).count(),
        "new_this_week": users.filter(date_joined__gte=week_ago).count(),
        "inactive_users": users.filter(is_active=False).count(),
        "recent_users": users.order_by("-date_joined")[:6],
    }
    return render(request, "adminpanel/dashboard.html", context)
