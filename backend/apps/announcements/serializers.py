from rest_framework import serializers
from .models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):
  '''公告转换json'''
  class Meta:
    model = Announcement
    fields = [
      "id",
      "title",
      "content",
      "is_active",
      "is_pinned",
      "created_at",
    ]
    read_only_fields = ["created_at"]
