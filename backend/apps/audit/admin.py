from django.contrib import admin

from .models import OperationLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "created_at",
    )
    list_filter = ("action", "method", "status_code", "created_at")
    search_fields = ("user__username", "path", "object_id")
    readonly_fields = (
        "user",
        "action",
        "method",
        "path",
        "status_code",
        "ip_address",
        "user_agent",
        "object_type",
        "object_id",
        "detail",
        "duration_ms",
        "created_at",
    )