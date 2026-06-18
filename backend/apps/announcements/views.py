from rest_framework import viewsets

from apps.problems.permissions import IsAdminOrReadOnly

from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
  serializer_class = AnnouncementSerializer
  permission_classes = [IsAdminOrReadOnly]
  search_fields = ("title", "content")
  ordering_fields = ("created_at", "is_pinned")

  def get_queryset(self):
    queryset = Announcement.objects.all()
    user = self.request.user
    if not (user.is_authenticated and user.is_admin):
      queryset = queryset.filter(is_active=True)
    return queryset
