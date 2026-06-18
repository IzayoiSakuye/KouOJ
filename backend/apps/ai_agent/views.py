from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ai_agent.models import AgentRun
from apps.ai_agent.serializers import AgentRunCreateSerializer, AgentRunReadSerializer
from apps.ai_agent.services import run_diagnostic_agent


class AgentRunViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    诊断型 agent 的后端 API。

    目前不改前端，但先把 REST 接口准备好：
    - POST /api/ai-agent/runs/ 创建并执行一次诊断
    - GET /api/ai-agent/runs/ 查看自己的诊断历史
    - GET /api/ai-agent/runs/{id}/ 查看某次诊断详情和步骤
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            AgentRun.objects.select_related("user", "submission", "submission__problem", "selected_solution")
            .prefetch_related("steps")
            .order_by("-id")
        )
        user = self.request.user
        if getattr(user, "is_admin", False):
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return AgentRunCreateSerializer
        return AgentRunReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = run_diagnostic_agent(
            user=request.user,
            submission_id=serializer.validated_data["submission_id"],
            hint_level=serializer.validated_data["hint_level"],
        )
        return Response(AgentRunReadSerializer(run).data, status=status.HTTP_201_CREATED)
