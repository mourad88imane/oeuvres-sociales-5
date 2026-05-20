import logging
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from core.serializers import BaseModelSerializer
from .models import (
    KpiDefinition, KpiSnapshot, DashboardWidget,
    ReportDefinition, ReportSchedule, DataExport,
)

logger = logging.getLogger("apps.reporting")


class KpiDefinitionSerializer(BaseModelSerializer):
    latest_value = serializers.SerializerMethodField()
    trend = serializers.SerializerMethodField()

    class Meta:
        model = KpiDefinition
        fields = [
            "id", "code", "name", "description", "category",
            "unit", "target_value", "formula", "is_active",
            "display_order", "metadata",
            "latest_value", "trend",
            "created_at", "updated_at",
        ]

    def get_latest_value(self, obj):
        snapshot = obj.snapshots.order_by("-date").first()
        if snapshot:
            return {
                "value": snapshot.value,
                "previous_value": snapshot.previous_value,
                "variation": snapshot.variation,
                "date": snapshot.date,
            }
        return None

    def get_trend(self, obj):
        snapshot = obj.snapshots.order_by("-date").first()
        if not snapshot or snapshot.variation is None:
            return "stable"
        if snapshot.variation > 5:
            return "up"
        if snapshot.variation < -5:
            return "down"
        return "stable"


class KpiSnapshotSerializer(BaseModelSerializer):
    kpi_code = serializers.CharField(source="kpi.code", read_only=True)
    kpi_name = serializers.CharField(source="kpi.name", read_only=True)
    kpi_unit = serializers.CharField(source="kpi.unit", read_only=True)

    class Meta:
        model = KpiSnapshot
        fields = [
            "id", "kpi", "kpi_code", "kpi_name", "kpi_unit",
            "value", "date", "previous_value", "variation", "metadata",
            "created_at",
        ]


class DashboardWidgetSerializer(BaseModelSerializer):
    widget_type_display = serializers.CharField(source="get_widget_type_display", read_only=True)
    size_display = serializers.CharField(source="get_size_display", read_only=True)

    class Meta:
        model = DashboardWidget
        fields = [
            "id", "user", "title", "widget_type", "widget_type_display",
            "size", "size_display", "config", "is_global",
            "display_order", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["user"]


class ReportDefinitionSerializer(BaseModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = ReportDefinition
        fields = [
            "id", "code", "title", "description", "category", "category_display",
            "default_format", "filters_config", "columns_config", "chart_config",
            "is_system", "is_active", "ai_insights_enabled",
            "created_at", "updated_at",
        ]


class ReportScheduleSerializer(BaseModelSerializer):
    report_title = serializers.CharField(source="report.title", read_only=True)
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)

    class Meta:
        model = ReportSchedule
        fields = [
            "id", "report", "report_title", "frequency", "frequency_display",
            "cron_expression", "recipients", "format", "export_format",
            "is_active", "last_run", "next_run", "filters_override",
            "created_at", "updated_at",
        ]


class DataExportSerializer(BaseModelSerializer):
    report_title = serializers.CharField(source="report.title", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    download_url = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DataExport
        fields = [
            "id", "report", "report_title", "export_format", "status", "status_display",
            "file", "download_url", "file_size", "filters_used",
            "row_count", "error_message", "completed_at", "duration_ms",
            "created_at", "created_by_name",
        ]

    def get_download_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class KpiSnapshotCreateSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


class ReportGenerateSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=ReportDefinition.FORMATS, default="excel")
    filters = serializers.JSONField(default=dict, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)


class AnalyticsFilterSerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    period = serializers.ChoiceField(
        choices=["7d", "30d", "90d", "6m", "1y", "all"],
        default="30d", required=False,
    )
    category = serializers.CharField(required=False)
