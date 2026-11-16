from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models
from django.templatetags.static import static


PH_MOBILE = RegexValidator(
    regex=r"^(09|\+639)\d{9}$",
    message="Enter a valid PH mobile number, e.g. 09171234567 or +639171234567.",
)


class RiderGuardUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Superusers created from the command line are RiderGuard admins.
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """RiderGuard account. Passwords are hashed by Django's auth system."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        RIDER = "RIDER", "Rider"

    class Platform(models.TextChoices):
        MAXIM = "MAXIM", "Maxim"
        MOVEIT = "MOVEIT", "MoveIt"
        GRAB = "GRAB", "Grab"
        LALAMOVE = "LALAMOVE", "Lalamove"
        FOODPANDA = "FOODPANDA", "Foodpanda"
        OTHER = "OTHER", "Other"

    class Vehicle(models.TextChoices):
        MOTORCYCLE = "MOTORCYCLE", "Motorcycle"
        CAR = "CAR", "Car"
        BICYCLE = "BICYCLE", "Bicycle"
        OTHER = "OTHER", "Other"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.RIDER)
    contact_number = models.CharField(max_length=13, blank=True, validators=[PH_MOBILE])
    city = models.CharField(max_length=80, blank=True)
    platforms = models.JSONField(default=list, blank=True, help_text="Platforms the rider works for.")
    vehicle_type = models.CharField(max_length=12, choices=Vehicle.choices, blank=True)
    plate_number = models.CharField(max_length=12, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True)

    objects = RiderGuardUserManager()

    class Meta:
        ordering = ["-date_joined"]

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_rider(self):
        return self.role == self.Role.RIDER

    @property
    def photo_url(self):
        if self.profile_photo:
            return self.profile_photo.url
        return static("img/avatar-default.svg")

    def get_platforms_display(self):
        labels = dict(self.Platform.choices)
        return ", ".join(labels.get(p, p) for p in self.platforms) or "None"

    def __str__(self):
        return self.get_full_name() or self.username
