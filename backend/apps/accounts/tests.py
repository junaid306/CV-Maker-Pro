import uuid

from rest_framework import status
from rest_framework.test import APITestCase

from apps.resumes.models import Resume
from .models import User
from .services import upgrade_guest


class AuthFlowTests(APITestCase):
    def test_register_login_me(self):
        response = self.client.post("/api/v1/auth/register/", {"email": "a@b.com", "password": "ChangeMe123", "name": "A"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "a@b.com")

    def test_guest_login_and_upgrade_preserves_data(self):
        guest = self.client.post("/api/v1/auth/guest/")
        self.assertEqual(guest.status_code, status.HTTP_201_CREATED)
        token = guest.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resume = Resume.objects.create(user=User.objects.get(pk=guest.data["user"]["id"]), title="My CV")
        upgraded = self.client.post("/api/v1/auth/upgrade-guest/", {"email": "real@x.com", "password": "ChangeMe123"})
        self.assertEqual(upgraded.status_code, 200)
        self.assertFalse(upgraded.data["user"]["is_guest"])
        resume.refresh_from_db()
        self.assertEqual(resume.user.email, "real@x.com")
        self.assertEqual(Resume.objects.filter(user=resume.user).count(), 1)

    def test_upgrade_to_taken_email_fails(self):
        User.objects.create_user(email="taken@x.com", password="OtherPass123")
        guest = self.client.post("/api/v1/auth/guest/")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {guest.data['access']}")
        response = self.client.post("/api/v1/auth/upgrade-guest/", {"email": "taken@x.com", "password": "ChangeMe123"})
        self.assertEqual(response.status_code, 400)
