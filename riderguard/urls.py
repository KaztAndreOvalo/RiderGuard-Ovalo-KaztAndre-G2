"""RiderGuard URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import TemplateView

from dashboard import views as dashboard_views

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", dashboard_views.dashboard_redirect, name="dashboard"),
    path("dashboard/", include("dashboard.urls")),
    path("panel/", include("adminpanel.urls")),
    path("trips/", include("trips.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
