from rest_framework import serializers

from apps.ai_agent.models import AgentRun, AgentStep


class AgentRunCreateSerializer(serializers.Serializer):
    """
    创建 agent 运行的入参。

    前端后续重构时只需要提交 submission_id 和 hint_level；后端会根据当前登录用户
    做权限校验，并在 service 层读取题目、提交、题解和 Tavily 搜索资料。
    """

    submission_id = serializers.IntegerField()
    hint_level = serializers.ChoiceField(choices=AgentRun.HintLevel.choices)


class AgentStepSerializer(serializers.ModelSerializer):
    """返回 agent 步骤摘要，便于调试和后续在管理端展示。"""

    class Meta:
        model = AgentStep
        fields = ("id", "step_type", "input_summary", "output_summary", "success", "created_at")


class AgentRunReadSerializer(serializers.ModelSerializer):
    """读取 agent 运行结果。"""

    steps = AgentStepSerializer(many=True, read_only=True)
    submission_id = serializers.IntegerField(source="submission.id", read_only=True)
    problem_title = serializers.CharField(source="submission.problem.title", read_only=True)
    selected_solution_title = serializers.CharField(source="selected_solution.title", read_only=True)

    class Meta:
        model = AgentRun
        fields = (
            "id",
            "submission_id",
            "problem_title",
            "hint_level",
            "status",
            "selected_solution",
            "selected_solution_title",
            "final_message",
            "confidence",
            "steps_count",
            "error_message",
            "steps",
            "created_at",
            "updated_at",
        )
