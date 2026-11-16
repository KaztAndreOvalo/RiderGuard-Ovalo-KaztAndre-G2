from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required
from accounts.models import User

from .forms import AdminUserCreateForm, AdminUserEditForm


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


@admin_required
def user_list(request):
    users = User.objects.all().order_by("-date_joined")
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q)
            | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if role in User.Role.values:
        users = users.filter(role=role)
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)

    page = Paginator(users, 10).get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)
    return render(request, "adminpanel/user_list.html", {
        "page": page, "q": q, "role": role, "status": status,
        "roles": User.Role.choices, "querystring": querystring.urlencode(),
    })


@admin_required
def user_detail(request, pk):
    member = get_object_or_404(User, pk=pk)
    return render(request, "adminpanel/user_detail.html", {"member": member})


@admin_required
def user_create(request):
    form = AdminUserCreateForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Account '{member.username}' created as {member.get_role_display()}.")
            return redirect("adminpanel:user_detail", pk=member.pk)
        messages.error(request, "Please correct the errors below.")
    return render(request, "adminpanel/user_form.html", {"form": form, "title": "Add user"})


@admin_required
def user_edit(request, pk):
    member = get_object_or_404(User, pk=pk)
    form = AdminUserEditForm(request.POST or None, instance=member, editor=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Account '{member.username}' updated.")
            return redirect("adminpanel:user_detail", pk=member.pk)
        messages.error(request, "Please correct the errors below.")
    return render(request, "adminpanel/user_form.html", {
        "form": form, "member": member, "title": f"Edit {member.username}",
    })


@admin_required
def user_set_password(request, pk):
    member = get_object_or_404(User, pk=pk)
    form = SetPasswordForm(member, request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Password for '{member.username}' has been reset.")
            return redirect("adminpanel:user_detail", pk=member.pk)
        messages.error(request, "Please correct the errors below.")
    return render(request, "adminpanel/user_form.html", {
        "form": form, "member": member, "title": f"Reset password for {member.username}",
    })


@admin_required
@require_POST
def user_toggle_active(request, pk):
    member = get_object_or_404(User, pk=pk)
    if member == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        member.is_active = not member.is_active
        member.save(update_fields=["is_active"])
        state = "activated" if member.is_active else "deactivated"
        messages.success(request, f"Account '{member.username}' {state}.")
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("adminpanel:users")


@admin_required
def user_delete(request, pk):
    member = get_object_or_404(User, pk=pk)
    if member == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("adminpanel:user_detail", pk=pk)
    if request.method == "POST":
        username = member.username
        member.delete()
        messages.success(request, f"Account '{username}' deleted.")
        return redirect("adminpanel:users")
    return render(request, "adminpanel/user_confirm_delete.html", {"member": member})
