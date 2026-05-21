"""Notification serializers."""

from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "channel",
            "channel_display",
            "priority",
            "priority_display",
            "is_read",
            "read_at",
            "action_url",
            "icon",
            "content_type",
            "object_id",
            "metadata",
            "time_ago",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_time_ago(self, obj):
        from django.utils import timezone

        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"Il y a {delta.days}j"
        if delta.seconds >= 3600:
            return f"Il y a {delta.seconds // 3600}h"
        if delta.seconds >= 60:
            return f"Il y a {delta.seconds // 60}min"
        return "À l'instant"


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "email_alerts",
            "sms_alerts",
            "push_alerts",
            "digest_frequency",
            "quiet_hours_start",
            "quiet_hours_end",
        ]


class MarkReadSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    all = serializers.BooleanField(default=False)
