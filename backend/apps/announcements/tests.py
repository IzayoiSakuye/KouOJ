from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Announcement


User = get_user_model()


class AnnouncementAPITests(APITestCase):
  def setUp(self):
    self.admin_user = User.objects.create_user(
      username="admin",
      password="admin-password",
      role=User.Role.ADMIN,
    )
    self.normal_user = User.objects.create_user(
      username="normal",
      password="normal-password",
    )
    self.active_announcement = Announcement.objects.create(
      title="Active",
      content="Visible announcement",
      is_active=True,
    )
    self.inactive_announcement = Announcement.objects.create(
      title="Inactive",
      content="Hidden announcement",
      is_active=False,
    )

  def test_anonymous_user_only_sees_active_announcements(self):
    response = self.client.get("/api/announcements/")

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    ids = [item["id"] for item in response.data["results"]]
    self.assertIn(self.active_announcement.id, ids)
    self.assertNotIn(self.inactive_announcement.id, ids)

  def test_normal_user_cannot_create_announcement(self):
    self.client.force_authenticate(self.normal_user)

    response = self.client.post(
      "/api/announcements/",
      {
        "title": "Blocked",
        "content": "Normal users cannot publish announcements",
        "is_active": True,
        "is_pinned": False,
      },
      format="json",
    )

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

  def test_role_admin_can_manage_announcements(self):
    self.client.force_authenticate(self.admin_user)

    create_response = self.client.post(
      "/api/announcements/",
      {
        "title": "Created",
        "content": "Created from the admin API",
        "is_active": True,
        "is_pinned": True,
      },
      format="json",
    )

    self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
    announcement_id = create_response.data["id"]

    update_response = self.client.patch(
      f"/api/announcements/{announcement_id}/",
      {"title": "Updated"},
      format="json",
    )
    self.assertEqual(update_response.status_code, status.HTTP_200_OK)
    self.assertEqual(update_response.data["title"], "Updated")

    delete_response = self.client.delete(f"/api/announcements/{announcement_id}/")
    self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
