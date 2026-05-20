from django.contrib import admin

from .models import JudgeResult, Submission


class JudgeResultInline(admin.TabularInline):
    model = JudgeResult
    extra = 0
    readonly_fields = ("testcase", "status", "time_used", "output", "error_message", "created_at")
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "problem", "language", "status", "score", "created_at")
    list_filter = ("status", "language", "created_at")
    search_fields = ("user__username", "problem__title", "code")
    readonly_fields = ("created_at", "judged_at")
    inlines = [JudgeResultInline]


@admin.register(JudgeResult)
class JudgeResultAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "testcase", "status", "time_used")
    list_filter = ("status",)
