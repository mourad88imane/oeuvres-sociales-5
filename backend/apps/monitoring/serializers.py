from rest_framework import serializers
from .models import APIRequestLog, SecurityEvent, BusinessMetric, APIEndpointStatus


class APIRequestLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default="")
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = APIRequestLog
        fields = [
            "id", "method", "endpoint", "status_code", "duration_ms",
            "is_error", "error_message", "user_email", "ip_address",
            "request_id", "time_ago", "timestamp",
        ]
        read_only_fields = fields

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)


class SecurityEventSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default="")
    resolved_by_email = serializers.EmailField(source="resolved_by.email", read_only=True, default="")
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = SecurityEvent
        fields = [
            "id", "event_type", "event_type_display", "severity", "severity_display",
            "user_email", "user_role", "ip_address", "endpoint", "details",
            "action_taken", "resolved", "resolved_at", "resolved_by_email",
            "resolution_note", "time_ago", "timestamp",
        ]
        read_only_fields = ["id", "timestamp", "resolved_at"]

    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)


class ResolveSecurityEventSerializer(serializers.Serializer):
    resolution_note = serializers.CharField(required=False, allow_blank=True)


class APIEndpointStatusSerializer(serializers.ModelSerializer):
    error_rate = serializers.SerializerMethodField()
    degraded_duration = serializers.SerializerMethodField()

    class Meta:
        model = APIEndpointStatus
        fields = [
            "endpoint", "method", "total_calls", "error_count", "error_rate",
            "avg_duration_ms", "max_duration_ms", "min_duration_ms",
            "last_called", "last_status", "is_degraded", "degraded_since",
            "degraded_duration",
        ]

    def get_error_rate(self, obj):
        if obj.total_calls == 0:
            return 0
        return round(obj.error_count / obj.total_calls * 100, 2)

    def get_degraded_duration(self, obj):
        if obj.degraded_since:
            from django.utils.timesince import timesince
            return timesince(obj.degraded_since)
        return None


class DashboardStatsSerializer(serializers.Serializer):
    total_calls = serializers.IntegerField()
    errors = serializers.IntegerField()
    error_rate = serializers.FloatField()
    avg_duration_ms = serializers.FloatField()
    top_endpoints = serializers.ListField()
    calls_by_hour = serializers.ListField()
    security_alerts = serializers.IntegerField()
    degraded_endpoints = serializers.IntegerField()
    top_users = serializers.ListField()


class BusinessMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessMetric
        fields = "__all__"
