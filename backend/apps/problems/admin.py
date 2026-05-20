from django.contrib import admin

from .models import Problem, Tag, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1
    fields = ("order", "input_data", "output_data", "is_sample", "score")


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "difficulty", "is_public", "created_at")
    list_filter = ("difficulty", "is_public", "tags")
    search_fields = ("title", "description")
    filter_horizontal = ("tags",)
    inlines = [TestCaseInline]

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "problem", "is_sample", "score", "order")
    list_filter = ("is_sample","problem")
