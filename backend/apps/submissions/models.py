from django.conf import settings
from django.db import models

from apps.problems.models import Problem, TestCase


class Submission(models.Model):
    class Language(models.TextChoices):
        PYTHON3 = "python3", "Python 3"

    class Status(models.TextChoices):
        PENDING = "PENDING", "等待判题"
        JUDGING = "JUDGING", "正在判题"
        ACCEPTED = "ACCEPTED", "答案正确"
        WRONG_ANSWER = "WRONG_ANSWER", "答案错误"
        TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED", "运行超时"
        RUNTIME_ERROR = "RUNTIME_ERROR", "运行错误"
        SYSTEM_ERROR = "SYSTEM_ERROR", "系统错误"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="submissions")
    language = models.CharField(max_length=20, choices=Language.choices, default=Language.PYTHON3)
    code = models.TextField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    score = models.PositiveIntegerField(default=0)
    time_used = models.PositiveIntegerField(default=0, help_text="单位：ms")
    memory_used = models.PositiveIntegerField(default=0, help_text="单位：KB")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    judged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"#{self.id} {self.user} {self.problem} {self.status}"


class JudgeResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="results")
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name="judge_results")
    status = models.CharField(max_length=30, choices=Submission.Status.choices)
    time_used = models.PositiveIntegerField(default=0)
    memory_used = models.PositiveIntegerField(default=0, help_text="单位：KB")
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"submission {self.submission_id} case {self.testcase_id}: {self.status}"
