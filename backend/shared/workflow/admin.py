from django.contrib import admin

from .models import WorkflowLog


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "content_type_name",
        "object_id",
        "from_state",
        "to_state",
        "actor_email",
        "actor_role",
        "is_reversal",
        "severity",
    ]
    list_filter = ["content_type_name", "to_state", "is_reversal", "severity"]
    search_fields = ["object_id", "actor_email", "reason"]
    readonly_fields = [f.name for f in WorkflowLog._meta.get_fields() if hasattr(f, "name")]

    def has_add_permission(self, r):
        return False

    def has_change_permission(self, r, obj=None):
        return False

    def has_delete_permission(self, r, obj=None):
        return False
