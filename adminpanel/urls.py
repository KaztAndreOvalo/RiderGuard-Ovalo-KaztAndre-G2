from django.urls import path

from . import fare_views, views

app_name = "adminpanel"

urlpatterns = [
    path("", views.admin_dashboard, name="dashboard"),
    path("users/", views.user_list, name="users"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/password/", views.user_set_password, name="user_set_password"),
    path("users/<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    # Fare Checker (admin side)
    path("rates/", fare_views.rate_list, name="rates"),
    path("rates/add/", fare_views.rate_create, name="rate_create"),
    path("rates/<int:pk>/edit/", fare_views.rate_edit, name="rate_edit"),
    path("rates/<int:pk>/delete/", fare_views.rate_delete, name="rate_delete"),
    path("trips/", fare_views.all_trips, name="trips"),
    path("trips/<int:pk>/", fare_views.trip_detail, name="trip_detail"),
]
