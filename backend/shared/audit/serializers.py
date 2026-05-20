from rest_framework import serializers
from .validation import ValidationTrace


class ValidationTraceSerializer(serializers.ModelSerializer):
    validated_by_email = serializers.EmailField(read_only=True, default="")
    time_ago = serializers.SerializerMethodField()
    validation_type_display = serializers.CharField(source="get_validation_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ValidationTrace
        fields = [
            "id", "validation_type", "validation_type_display", "status", "status_display",
            "validated_by_email", "validated_by_role", "object_repr",
            "comment", "evidence", "ip_address",
            "requires_second_approval", "second_approval_at",
            "expiry_date", "is_expired",
            "request_id", "time_ago", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)
