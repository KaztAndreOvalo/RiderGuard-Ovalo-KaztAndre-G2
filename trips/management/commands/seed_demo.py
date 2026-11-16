"""
Create demo data for testing and grading:

  python manage.py seed_demo

- Test accounts (test passwords only): demo_admin and demo_rider
- Sample reference commission rates (clearly labelled as samples)
- A handful of trips for demo_rider, some of which the Fare Checker flags

Safe to run more than once: existing demo accounts and rates are reused,
and demo_rider's trips are recreated.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from trips.models import CommissionRate, Platform, Trip

DEMO_PASSWORD_ADMIN = "AdminDemo#2026"
DEMO_PASSWORD_RIDER = "RiderDemo#2026"
SAMPLE_NOTE = "Sample rate for testing; verify against the platform's published rate."

SAMPLE_RATES = [
    ("MAXIM", "RIDE", "15.00"),
    ("MAXIM", "DELIVERY", "15.00"),
    ("MOVEIT", "RIDE", "20.00"),
    ("GRAB", "RIDE", "20.00"),
    ("GRAB", "FOOD", "20.00"),
    ("LALAMOVE", "DELIVERY", "20.00"),
    ("FOODPANDA", "FOOD", "20.00"),
]

# (days ago, platform, service, pickup, dropoff, km, gross, commission, other, tips, net)
SAMPLE_TRIPS = [
    (0, "MAXIM", "RIDE", "SM City Cebu", "IT Park, Lahug", "6.2", "185.00", "27.75", "0", "0", "157.25"),
    (1, "MAXIM", "RIDE", "Ayala Center Cebu", "Mactan Airport", "14.8", "420.00", "92.40", "0", "20.00", "347.60"),
    (1, "MOVEIT", "RIDE", "Colon St.", "Talamban", "8.1", "210.00", "42.00", "0", "0", "168.00"),
    (2, "GRAB", "FOOD", "Jollibee Mabolo", "Banilad Town Centre", "4.5", "95.00", "19.00", "5.00", "10.00", "81.00"),
    (3, "MAXIM", "DELIVERY", "Carbon Market", "Guadalupe", "5.0", "120.00", "18.00", "0", "0", "92.00"),
    (4, "MOVEIT", "RIDE", "SM Seaside", "Talisay City", "9.6", "260.00", "52.00", "0", "0", "208.00"),
    (6, "OTHER", "DELIVERY", "Mandaue City Hall", "Consolacion", "7.3", "150.00", "30.00", "0", "0", "120.00"),
]


class Command(BaseCommand):
    help = "Create demo accounts, sample reference rates and sample trips."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._user("demo_admin", "demo_admin@riderguard.test", DEMO_PASSWORD_ADMIN,
                           role=User.Role.ADMIN, first_name="Demo", last_name="Admin")
        rider = self._user("demo_rider", "demo_rider@riderguard.test", DEMO_PASSWORD_RIDER,
                           role=User.Role.RIDER, first_name="Juan", last_name="Dela Cruz",
                           platforms=["MAXIM", "MOVEIT", "GRAB"], city="Cebu City",
                           vehicle_type=User.Vehicle.MOTORCYCLE, plate_number="ABC 1234",
                           contact_number="09171234567")

        effective = date(timezone.localdate().year, 1, 1)
        for code, service, percent in SAMPLE_RATES:
            CommissionRate.objects.get_or_create(
                platform=Platform.objects.get(code=code), service_type=service, effective_from=effective,
                defaults={"commission_percent": Decimal(percent), "source_note": SAMPLE_NOTE, "created_by": admin},
            )

        Trip.objects.filter(rider=rider).delete()
        today = timezone.localdate()
        for days, code, service, pickup, dropoff, km, gross, comm, other, tips, net in SAMPLE_TRIPS:
            Trip.objects.create(
                rider=rider, platform=Platform.objects.get(code=code), service_type=service,
                trip_date=today - timedelta(days=days), pickup_location=pickup, dropoff_location=dropoff,
                distance_km=Decimal(km), gross_fare=Decimal(gross), commission_deducted=Decimal(comm),
                other_deductions=Decimal(other), tips=Decimal(tips), net_received=Decimal(net),
            )

        flagged = Trip.objects.filter(rider=rider, check_status=Trip.CheckStatus.FLAGGED).count()
        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {CommissionRate.objects.count()} rates, "
            f"{Trip.objects.filter(rider=rider).count()} trips for demo_rider ({flagged} flagged)."
        ))
        self.stdout.write("  Admin: demo_admin / " + DEMO_PASSWORD_ADMIN)
        self.stdout.write("  Rider: demo_rider / " + DEMO_PASSWORD_RIDER)

    def _user(self, username, email, password, **fields):
        user = User.objects.filter(username=username).first() or User(username=username)
        user.email = email
        for key, value in fields.items():
            setattr(user, key, value)
        user.is_active = True
        user.set_password(password)
        user.save()
        return user
