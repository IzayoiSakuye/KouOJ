from django.conf import settings
from django.db import models


class AgentRun(models.Model):
    """
    记录一次 AI 诊断运行。

    这个模型是后端 agent 的“主记录”：学生点一次 AI 诊断，就创建一条 AgentRun。
    它保存最终要展示给学生的提示，也保存 agent 在本轮运行中选择的参考题解、
    运行状态和步数，方便后续做历史记录、排查问题和成本统计。
    """

    class HintLevel(models.TextChoices):
        DIRECTION = "direction", "方向提示"
        LOCATE = "locate", "定位问题"
        EXPLAIN = "explain", "详细解释"

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "运行中"
        COMPLETED = "COMPLETED", "已完成"
        FAILED = "FAILED", "运行失败"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_runs",
    )
    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="agent_runs",
    )
    hint_level = models.CharField(max_length=20, choices=HintLevel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    selected_solution = models.ForeignKey(
        "solutions.Solution",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agent_runs",
    )
    final_message = models.TextField(blank=True)
    confidence = models.PositiveIntegerField(default=0)
    steps_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"AgentRun #{self.id} submission #{self.submission_id} {self.status}"


class AgentStep(models.Model):
    """
    记录 agent 运行中的一个步骤。

    v1 使用 LangGraph 编排 agent 流程：读取上下文 -> 读取本地题解 -> Tavily 搜索 ->
    生成提示。每一步都写入 AgentStep，这样后面如果诊断结果不准，我们能看到 agent
    当时拿到了什么材料、走到了图里的哪个节点，而不是只剩一段最终文本。
    """

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="steps")
    step_type = models.CharField(max_length=40)
    input_summary = models.TextField(blank=True)
    output_summary = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"AgentRun #{self.run_id} step {self.step_type}"
