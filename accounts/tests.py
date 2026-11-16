from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = "Str0ng-Pass!2026"


def make_user(username, role=User.Role.RIDER, **extra):
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD,
        first_name=username.title(), last_name="Test", role=role, **extra,
    )


class RegistrationTests(TestCase):
    def post(self, **overrides):
        data = {
            "first_name": "Juan", "last_name": "Dela Cruz", "username": "juandc",
            "email": "juan@example.com", "contact_number": "09171234567",
            "platforms": ["MAXIM", "GRAB"], "password1": PASSWORD, "password2": PASSWORD,
        }
        data.update(overrides)
        return self.client.post(reverse("accounts:register"), data, follow=True)

    def test_register_creates_rider_with_hashed_password(self):
        response = self.post()
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(response, "Account created")
        user = User.objects.get(username="juandc")
        self.assertEqual(user.role, User.Role.RIDER)
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertEqual(user.platforms, ["MAXIM", "GRAB"])

    def test_required_fields(self):
        response = self.post(first_name="", email="", platforms=[])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertContains(response, "This field is required.", count=3)

    def test_invalid_email(self):
        self.post(email="not-an-email")
        self.assertFalse(User.objects.exists())

    def test_duplicate_username_and_email(self):
        make_user("juandc")
        response = self.post(email="juandc@example.com")
        self.assertContains(response, "This username is already taken.")
        self.assertContains(response, "An account with this email already exists.")
        self.assertEqual(User.objects.count(), 1)

    def test_password_mismatch(self):
        response = self.post(password2="Different-Pass!1")
        self.assertContains(response, "password fields didn")
        self.assertFalse(User.objects.exists())

    def test_cannot_self_register_as_admin(self):
        self.post(role="ADMIN")
        self.assertEqual(User.objects.get().role, User.Role.RIDER)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.rider = make_user("rider1")
        self.admin = make_user("admin1", role=User.Role.ADMIN)

    def login(self, username, password=PASSWORD):
        return self.client.post(reverse("accounts:login"), {"username": username, "password": password}, follow=True)

    def test_invalid_credentials_show_error(self):
        response = self.login("rider1", "wrong-password")
        self.assertContains(response, "Invalid username/email or password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_rider_lands_on_rider_dashboard(self):
        response = self.login("rider1")
        self.assertRedirects(response, reverse("dashboard:rider"), fetch_redirect_response=True)

    def test_admin_lands_on_admin_dashboard(self):
        response = self.login("admin1")
        self.assertRedirects(response, reverse("adminpanel:dashboard"))

    def test_login_with_email(self):
        response = self.login("rider1@example.com")
        self.assertRedirects(response, reverse("dashboard:rider"))

    def test_deactivated_user_cannot_login(self):
        self.rider.is_active = False
        self.rider.save()
        self.login("rider1")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_ends_session(self):
        self.client.force_login(self.rider)
        response = self.client.post(reverse("accounts:logout"), follow=True)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class AccessControlTests(TestCase):
    def setUp(self):
        self.rider = make_user("rider1")
        self.admin = make_user("admin1", role=User.Role.ADMIN)

    def test_logged_out_user_redirected_to_login(self):
        for name in ("dashboard", "dashboard:rider", "adminpanel:dashboard", "adminpanel:users", "accounts:profile"):
            url = reverse(name)
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}", fetch_redirect_response=False)

    def test_rider_cannot_open_admin_pages(self):
        self.client.force_login(self.rider)
        for url in (reverse("adminpanel:dashboard"), reverse("adminpanel:users"),
                    reverse("adminpanel:user_edit", args=[self.admin.pk])):
            response = self.client.get(url)
            self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_admin_cannot_open_rider_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:rider"))
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)


class ProfileTests(TestCase):
    def setUp(self):
        self.rider = make_user("rider1")
        self.other = make_user("rider2")
        self.client.force_login(self.rider)

    def test_profile_shows_only_own_data(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "rider1@example.com")
        self.assertNotContains(response, "rider2@example.com")

    def test_update_profile(self):
        response = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "New", "last_name": "Name", "email": "new@example.com",
            "contact_number": "09181234567", "city": "Cebu City",
            "platforms": ["MOVEIT"], "vehicle_type": "MOTORCYCLE", "plate_number": "abc 1234",
        }, follow=True)
        self.assertContains(response, "Your profile has been updated.")
        self.rider.refresh_from_db()
        self.assertEqual(self.rider.first_name, "New")
        self.assertEqual(self.rider.plate_number, "ABC 1234")
        self.other.refresh_from_db()
        self.assertEqual(self.other.first_name, "Rider2")

    def test_cannot_take_another_users_email(self):
        response = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "X", "last_name": "Y", "email": "rider2@example.com",
        })
        self.assertContains(response, "An account with this email already exists.")

    def test_invalid_phone_rejected(self):
        response = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "X", "last_name": "Y", "email": "rider1@example.com", "contact_number": "12345",
        })
        self.assertContains(response, "valid PH mobile number")
