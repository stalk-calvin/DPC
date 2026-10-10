from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .factories import make_product, make_tag


class AdminSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            "admin", "a@example.com", "pw"
        )
        make_product(tags=(make_tag(),))

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_changelist_and_add_pages_render(self):
        for model in ("category", "tag", "product"):
            for page in ("changelist", "add"):
                with self.subTest(model=model, page=page):
                    response = self.client.get(reverse(f"admin:catalog_{model}_{page}"))
                    self.assertEqual(response.status_code, 200)

    def test_duplicate_category_shows_friendly_error(self):
        url = reverse("admin:catalog_category_add")

        with self.assertLogs("catalog.admin", "INFO") as logs:
            self.client.post(url, {"name": "Garden"})
        self.assertEqual(
            logs.output,
            ["INFO:catalog.admin:Admin 'admin' on catalog.category 'Garden': Added."],
        )
        response = self.client.post(url, {"name": "garden"})
        self.assertContains(response, "An entry with this name already exists.")


class AdminLoginMessageTests(TestCase):
    def test_wrong_password_and_non_staff_get_the_same_clear_message(self):
        get_user_model().objects.create_user("calvin", password="right-pw")

        with self.assertLogs("catalog.admin", "WARNING") as logs:
            for password in ("wrong-pw", "right-pw"):
                with self.subTest(password=password):
                    response = self.client.post(
                        reverse("admin:login"),
                        {"username": "calvin", "password": password},
                    )
                    self.assertContains(response, "does not have admin access")
        self.assertEqual(
            logs.output, ["WARNING:catalog.admin:Login failed for username 'calvin'"]
        )
