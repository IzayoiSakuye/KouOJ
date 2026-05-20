from rest_framework import serializers

from apps.problems.models import Problem
from .models import JudgeResult, Submission


class JudgeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = JudgeResult
        fields = ("id", "testcase", "status", "time_used", "memory_used", "output", "error_message")


class SubmissionCreateSerializer(serializers.ModelSerializer):
    problem = serializers.PrimaryKeyRelatedField(queryset=Problem.objects.filter(is_public=True))

    class Meta:
        model = Submission
        fields = ("id", "problem", "language", "code")

    def create(self, validated_data):
        user = self.context["request"].user
        user.submit_count += 1
        user.save(update_fields=["submit_count"])
        return Submission.objects.create(user=user, **validated_data)


class SubmissionReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    results = JudgeResultSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id",
            "username",
            "problem",
            "problem_title",
            "language",
            "code",
            "status",
            "score",
            "time_used",
            "memory_used",
            "error_message",
            "results",
            "created_at",
            "judged_at",
        )
