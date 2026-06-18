from django.contrib import admin

from .models import AgentRun, AgentStep


class AgentStepInline(admin.TabularInline):
    model = AgentStep
    extra = 0
    readonly_fields = ("step_type", "input_summary", "output_summary", "success", "created_at")


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "submission", "hint_level", "status", "confidence", "created_at")
    list_filter = ("hint_level", "status")
    search_fields = ("user__username", "submission__problem__title", "final_message")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AgentStepInline]


@admin.register(AgentStep)
class AgentStepAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "step_type", "success", "created_at")
    list_filter = ("step_type", "success")
    search_fields = ("input_summary", "output_summary")
