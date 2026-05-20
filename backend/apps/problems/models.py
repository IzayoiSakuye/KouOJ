from django.conf import settings
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Problem(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "简单"
        MEDIUM = "medium", "中等"
        HARD = "hard", "困难"

    title = models.CharField(max_length=120)
    description = models.TextField()
    input_description = models.TextField(blank=True)
    output_description = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
    )
    time_limit = models.PositiveIntegerField(default=2000, help_text="单位：ms")
    memory_limit = models.PositiveIntegerField(default=128, help_text="单位：MB")
    is_public = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="problems")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_problems",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.id}. {self.title}"


class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="test_cases")
    input_data = models.TextField(blank=True)
    output_data = models.TextField(blank=True)
    is_sample = models.BooleanField(default=False)
    score = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.problem_id} - case {self.id}"
