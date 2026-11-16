from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import User


def role_required(*roles):
    """
    Allow a view only for logged-in users with one of the given roles.

    Logged-out users go to the login page (via @login_required).
    Logged-in users with the wrong role are sent back to their own dashboard,
    so typing another role's URL never opens that role's pages.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to open that page.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


rider_required = role_required(User.Role.RIDER)
admin_required = role_required(User.Role.ADMIN)
