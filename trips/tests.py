from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Platform, Trip

PASSWORD = "Str0ng-Pass!2026"


def make_user(username, role=User.Role.RIDER):
    return User.objects.create_user(username, f"{username}@example.com", PASSWORD, role=role)


def trip_data(**overrides):
    data = {
        "platform": Platform.objects.get(code="MAXIM").pk,
        "service_type": "RIDE",
        "trip_date": timezone.localdate().isoformat(),
        "pickup_location": "SM City Cebu",
        "dropoff_location": "IT Park",
        "distance_km": "6.5",
        "gross_fare": "200.00",
        "commission_deducted": "30.00",
        "other_deductions": "5.00",
        "tips": "0.00",
        "net_received": "165.00",
        "notes": "",
    }
    data.update(overrides)
    return data


class TripTestCase(TestCase):
    def setUp(self):
        self.rider = make_user("rider1")
        self.other = make_user("rider2")
        self.admin = make_user("admin1", role=User.Role.ADMIN)
        self.maxim = Platform.objects.get(code="MAXIM")

    def make_trip(self, rider=None, **extra):
        values = {
            "rider": rider or self.rider, "platform": self.maxim, "service_type": "RIDE",
            "trip_date": timezone.localdate(), "pickup_location": "A", "dropoff_location": "B",
            "gross_fare": Decimal("200"), "commission_deducted": Decimal("30"),
            "other_deductions": Decimal("0"), "net_received": Decimal("170"),
        }
        values.update(extra)
        return Trip.objects.create(**values)


class TripCrudTests(TripTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.rider)

    def test_create_trip_linked_to_rider(self):
        response = self.client.post(reverse("trips:create"), trip_data(), follow=True)
        trip = Trip.objects.get()
        self.assertEqual(trip.rider, self.rider)
        self.assertRedirects(response, reverse("trips:detail", args=[trip.pk]))
        self.assertContains(response, "Trip logged successfully.")

    def test_list_shows_only_own_trips(self):
        self.make_trip(pickup_location="Mine")
        self.make_trip(rider=self.other, pickup_location="NotMine")
        response = self.client.get(reverse("trips:list"))
        self.assertContains(response, "Mine")
        self.assertNotContains(response, "NotMine")

    def test_update_trip(self):
        trip = self.make_trip()
        response = self.client.post(reverse("trips:edit", args=[trip.pk]), trip_data(gross_fare="250.00", net_received="215.00"), follow=True)
        self.assertContains(response, "Trip updated.")
        trip.refresh_from_db()
        self.assertEqual(trip.gross_fare, Decimal("250.00"))

    def test_delete_trip(self):
        trip = self.make_trip()
        response = self.client.post(reverse("trips:delete", args=[trip.pk]), follow=True)
        self.assertContains(response, "Trip deleted.")
        self.assertFalse(Trip.objects.exists())

    def test_cannot_view_edit_or_delete_another_riders_trip(self):
        trip = self.make_trip(rider=self.other)
        for name in ("trips:detail", "trips:edit", "trips:delete"):
            self.assertEqual(self.client.get(reverse(name, args=[trip.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("trips:delete", args=[trip.pk])).status_code, 404)
        self.assertTrue(Trip.objects.filter(pk=trip.pk).exists())

    def test_filter_by_platform(self):
        self.make_trip(pickup_location="MaximTrip")
        self.make_trip(platform=Platform.objects.get(code="GRAB"), pickup_location="GrabTrip")
        response = self.client.get(reverse("trips:list"), {"platform": self.maxim.pk})
        self.assertContains(response, "MaximTrip")
        self.assertNotContains(response, "GrabTrip")

    def test_dashboard_shows_weekly_earnings(self):
        self.make_trip(net_received=Decimal("170"))
        self.make_trip(net_received=Decimal("80.50"))
        response = self.client.get(reverse("dashboard:rider"))
        self.assertContains(response, "₱250.50")


class TripValidationTests(TripTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.rider)

    def post(self, **overrides):
        return self.client.post(reverse("trips:create"), trip_data(**overrides))

    def assert_rejected(self, response, message):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, message)
        self.assertFalse(Trip.objects.exists())

    def test_required_fields(self):
        response = self.post(platform="", pickup_location="", gross_fare="", net_received="")
        self.assert_rejected(response, "This field is required.")

    def test_future_date(self):
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        self.assert_rejected(self.post(trip_date=tomorrow), "Trip date cannot be in the future.")

    def test_zero_gross_fare(self):
        self.assert_rejected(self.post(gross_fare="0"), "Gross fare must be greater than")

    def test_commission_more_than_gross(self):
        self.assert_rejected(self.post(commission_deducted="250"), "Commission cannot be more than the gross fare.")

    def test_net_more_than_gross(self):
        self.assert_rejected(self.post(net_received="500"), "Net received cannot be more than")

    def test_negative_amount(self):
        self.assert_rejected(self.post(other_deductions="-5"), "cannot be negative")

    def test_same_pickup_and_dropoff(self):
        self.assert_rejected(self.post(dropoff_location="sm city cebu"), "must be different from the pickup")

    def test_invalid_number_format(self):
        self.assert_rejected(self.post(gross_fare="abc"), "Enter a number.")


class TripAccessTests(TripTestCase):
    def test_logged_out_redirected_to_login(self):
        url = reverse("trips:list")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}", fetch_redirect_response=False)

    def test_admin_cannot_use_rider_trip_logger(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("trips:create"))
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
