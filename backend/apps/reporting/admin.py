from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    KpiDefinition, KpiSnapshot, DashboardWidget,
    ReportDefinition, ReportSchedule, DataExport,
)


class KpiSnapshotInline(admin.TabularInline):
    model = KpiSnapshot
    extra = 0
    fields = ["value", "date", "previous_value", "variation"]
    readonly_fields = ["value", "date", "previous_value", "variation"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(KpiDefinition)
class KpiDefinitionAdmin(SimpleHistoryAdmin):
    list_display = ["code", "name", "category", "unit", "target_value", "is_active", "display_order"]
    list_filter = ["category", "is_active"]
    search_fields = ["code", "name"]
    ordering = ["category", "display_order"]
    inlines = [KpiSnapshotInline]


@admin.register(KpiSnapshot)
class KpiSnapshotAdmin(SimpleHistoryAdmin):
    list_display = ["kpi", "value", "variation", "date", "created_at"]
    list_filter = ["date", "kpi__category"]
    search_fields = ["kpi__code", "kpi__name"]
    ordering = ["-date"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(SimpleHistoryAdmin):
    list_display = ["title", "widget_type", "size", "is_global", "is_active", "display_order", "user"]
    list_filter = ["widget_type", "is_global", "is_active"]
    search_fields = ["title"]
    ordering = ["display_order"]


@admin.register(ReportDefinition)
class ReportDefinitionAdmin(SimpleHistoryAdmin):
    list_display = ["code", "title", "category", "default_format", "is_system", "is_active"]
    list_filter = ["category", "default_format", "is_system", "is_active"]
    search_fields = ["code", "title"]
    ordering = ["category", "title"]


@admin.register(ReportSchedule)
class ReportScheduleAdmin(SimpleHistoryAdmin):
    list_display = ["report", "frequency", "format", "is_active", "last_run", "next_run"]
    list_filter = ["frequency", "format", "is_active"]
    search_fields = ["report__title", "report__code"]


@admin.register(DataExport)
class DataExportAdmin(SimpleHistoryAdmin):
    list_display = ["report", "export_format", "status", "row_count", "file_size", "completed_at", "created_at"]
    list_filter = ["status", "export_format"]
    search_fields = ["report__title", "report__code"]

    def has_add_permission(self, request, obj=None):
        return False
