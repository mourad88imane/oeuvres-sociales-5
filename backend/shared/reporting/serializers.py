"""Reporting engine — base serializers."""

from rest_framework import serializers


class BaseReportDefinitionSerializer(serializers.ModelSerializer):
    """Concrete serializer for ReportDefinition models."""

    class Meta:
        fields = [
            "id",
            "code",
            "title",
            "description",
            "category",
            "default_format",
            "filters_config",
            "columns_config",
            "chart_config",
            "is_system",
            "is_active",
            "ai_insights_enabled",
        ]


class BaseReportScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "frequency",
            "cron_expression",
            "recipients",
            "format",
            "is_active",
            "last_run",
            "next_run",
            "filters_override",
        ]


class BaseDataExportSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "export_format",
            "status",
            "file",
            "file_size",
            "filters_used",
            "row_count",
            "error_message",
            "completed_at",
            "duration_ms",
        ]


class BaseKpiDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "code",
            "name",
            "description",
            "category",
            "unit",
            "target_value",
            "formula",
            "is_active",
            "display_order",
            "metadata",
        ]


class BaseKpiSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "kpi",
            "value",
            "date",
            "previous_value",
            "variation",
            "metadata",
        ]


class BaseDashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            "id",
            "title",
            "widget_type",
            "size",
            "config",
            "is_global",
            "display_order",
            "is_active",
        ]
