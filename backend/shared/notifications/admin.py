from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient", "channel", "priority", "is_read", "read_at", "created_at"]
    list_filter = ["channel", "priority", "is_read"]
    search_fields = ["title", "body", "recipient__username", "recipient__email"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "email_alerts", "sms_alerts", "push_alerts", "digest_frequency"]
    list_filter = ["email_alerts", "digest_frequency"]
    search_fields = ["user__username", "user__email"]
