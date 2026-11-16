from django.test import TestCase
from django.urls import reverse

from accounts.models import User

PASSWORD = "Str0ng-Pass!2026"


class AdminPanelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin1", "admin1@example.com", PASSWORD, role=User.Role.ADMIN)
        self.rider = User.objects.create_user("rider1", "rider1@example.com", PASSWORD)
        self.client.force_login(self.admin)

    def test_user_list_search(self):
        response = self.client.get(reverse("adminpanel:users"), {"q": "rider1"})
        self.assertContains(response, "rider1@example.com")
        self.assertNotContains(response, "admin1@example.com")

    def test_create_admin_user(self):
        response = self.client.post(reverse("adminpanel:user_create"), {
            "first_name": "Ana", "last_name": "Admin", "username": "ana", "email": "ana@example.com",
            "role": "ADMIN", "password1": PASSWORD, "password2": PASSWORD,
        })
        ana = User.objects.get(username="ana")
        self.assertRedirects(response, reverse("adminpanel:user_detail", args=[ana.pk]))
        self.assertEqual(ana.role, User.Role.ADMIN)

    def test_toggle_active(self):
        self.client.post(reverse("adminpanel:user_toggle_active", args=[self.rider.pk]))
        self.rider.refresh_from_db()
        self.assertFalse(self.rider.is_active)

    def test_cannot_deactivate_self(self):
        self.client.post(reverse("adminpanel:user_toggle_active", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_delete_user(self):
        self.client.post(reverse("adminpanel:user_delete", args=[self.rider.pk]))
        self.assertFalse(User.objects.filter(pk=self.rider.pk).exists())

    def test_django_admin_is_not_installed(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_superuser_gets_admin_role(self):
        su = User.objects.create_superuser("root", "root@example.com", PASSWORD)
        self.assertEqual(su.role, User.Role.ADMIN)
