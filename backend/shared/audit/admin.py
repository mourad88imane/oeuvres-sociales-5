"""Audit admin — lecture seule."""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp", "user_email", "user_role",
        "action", "severity", "content_type_name", "object_repr", "ip_address",
    ]
    list_filter = ["action", "severity", "user_role", "timestamp"]
    search_fields = ["user_email", "object_repr", "ip_address", "content_type_name"]
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False  # Pas de création manuelle

    def has_change_permission(self, request, obj=None):
        return False  # Immuable

    def has_delete_permission(self, request, obj=None):
        return False  # Jamais supprimé
