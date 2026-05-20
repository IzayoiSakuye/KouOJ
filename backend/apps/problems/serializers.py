from rest_framework import serializers

from .models import Problem, Tag, TestCase


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class SampleCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ("id", "input_data", "output_data", "order")


class ProblemListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = (
            "id",
            "title",
            "difficulty",
            "time_limit",
            "memory_limit",
            "tags",
        )


class ProblemDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags",
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )
    sample_cases = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = (
            "id",
            "title",
            "description",
            "input_description",
            "output_description",
            "difficulty",
            "time_limit",
            "memory_limit",
            "is_public",
            "tags",
            "tag_ids",
            "sample_cases",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_sample_cases(self, obj):
        samples = obj.test_cases.filter(is_sample=True)
        return SampleCaseSerializer(samples, many=True).data


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ("id", "problem", "input_data", "output_data", "is_sample", "score", "order")
