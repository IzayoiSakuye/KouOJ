from rest_framework import viewsets
from .models import Problem, Tag, TestCase
from .permissions import IsAdminOrReadOnly, IsOJAdmin
from .serializers import (
    ProblemDetailSerializer,
    ProblemListSerializer,
    TagSerializer,
    TestCaseSerializer,
)


class ProblemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ("difficulty", "tags")
    search_fields = ("title", "description")
    ordering_fields = ("id", "created_at", "difficulty")

    def get_queryset(self):
        queryset = Problem.objects.prefetch_related("tags", "test_cases")
        user = self.request.user
        if not (user.is_authenticated and user.is_admin):
            queryset = queryset.filter(is_public=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ProblemListSerializer
        return ProblemDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ("name",)


class TestCaseViewSet(viewsets.ModelViewSet):
    serializer_class = TestCaseSerializer
    permission_classes = [IsOJAdmin]
    filterset_fields = ("problem", "is_sample")
    ordering_fields = ("id", "order")

    def get_queryset(self):
        return TestCase.objects.select_related("problem")
