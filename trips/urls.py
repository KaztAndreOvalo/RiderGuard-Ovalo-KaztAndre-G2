from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.trip_list, name="list"),
    path("new/", views.trip_create, name="create"),
    path("<int:pk>/", views.trip_detail, name="detail"),
    path("<int:pk>/edit/", views.trip_edit, name="edit"),
    path("<int:pk>/delete/", views.trip_delete, name="delete"),
]
