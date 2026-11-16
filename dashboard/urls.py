from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("rider/", views.rider_dashboard, name="rider"),
]
