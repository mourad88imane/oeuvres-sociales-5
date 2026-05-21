from django.contrib import admin

from .models import APIEndpointStatus, APIRequestLog, BusinessMetric, SecurityEvent


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "method",
        "endpoint",
        "status_code",
        "duration_ms",
        "is_error",
        "user",
    ]
    list_filter = ["method", "is_error", "status_code", "timestamp"]
    search_fields = ["endpoint", "error_message"]
    readonly_fields = [f.name for f in APIRequestLog._meta.get_fields()]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "event_type", "severity", "user_email", "ip_address", "resolved"]
    list_filter = ["event_type", "severity", "resolved", "timestamp"]
    search_fields = ["user_email", "ip_address", "details"]
    readonly_fields = [f.name for f in SecurityEvent._meta.get_fields()]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(BusinessMetric)
class BusinessMetricAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "metric_type", "granularity", "value", "label"]
    list_filter = ["metric_type", "granularity", "timestamp"]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]


@admin.register(APIEndpointStatus)
class APIEndpointStatusAdmin(admin.ModelAdmin):
    list_display = [
        "endpoint",
        "method",
        "total_calls",
        "error_count",
        "avg_duration_ms",
        "is_degraded",
    ]
    list_filter = ["is_degraded", "method"]
    search_fields = ["endpoint"]
    ordering = ["-total_calls"]
