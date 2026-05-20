from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Submission
from .serializers import SubmissionCreateSerializer, SubmissionReadSerializer


class SubmissionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    filterset_fields = ("problem", "status", "language")
    ordering_fields = ("id", "created_at")

    def get_queryset(self):
        queryset = Submission.objects.select_related("user", "problem").prefetch_related("results")
        user = self.request.user
        if user.is_admin:
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissionCreateSerializer
        return SubmissionReadSerializer
