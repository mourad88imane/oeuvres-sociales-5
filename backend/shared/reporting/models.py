"""Reporting engine — generic report definitions, schedules, exports, KPIs, widgets."""

from django.conf import settings
from django.db import models


class BaseReportDefinition(models.Model):
    """Abstract base for report definitions — subclass per project."""

    FORMATS = [
        ("excel", "Excel"),
        ("csv", "CSV"),
        ("pdf", "PDF"),
        ("json", "JSON"),
    ]
    CATEGORIES = getattr(
        settings,
        "REPORT_CATEGORIES",
        [
            ("employees", "Employés"),
            ("benefits", "Prestations"),
            ("finance", "Finance"),
            ("conventions", "Conventions"),
            ("kpi", "Indicateurs KPI"),
            ("custom", "Personnalisé"),
        ],
    )
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    default_format = models.CharField(max_length=10, choices=FORMATS, default="excel")
    filters_config = models.JSONField(default=dict, blank=True)
    columns_config = models.JSONField(default=list, blank=True)
    chart_config = models.JSONField(default=dict, blank=True)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ai_insights_enabled = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["category", "title"]

    def __str__(self):
        return f"{self.title} ({self.code})"


class BaseReportSchedule(models.Model):
    """Abstract base for scheduled reports."""

    FREQUENCIES = [
        ("daily", "Quotidien"),
        ("weekly", "Hebdomadaire"),
        ("monthly", "Mensuel"),
        ("quarterly", "Trimestriel"),
        ("yearly", "Annuel"),
        ("custom", "Personnalisé"),
    ]

    frequency = models.CharField(max_length=15, choices=FREQUENCIES)
    cron_expression = models.CharField(max_length=100, blank=True)
    recipients = models.JSONField(default=list, blank=True)
    format = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    filters_override = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        ordering = ["next_run"]

    def __str__(self):
        return f"{self.frequency} — dernier: {self.last_run}"


class BaseDataExport(models.Model):
    """Abstract base for data exports."""

    STATUSES = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
    ]
    export_format = models.CharField(max_length=10)
    file = models.FileField(upload_to="exports/%Y/%m/", null=True, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUSES, default="pending")
    filters_used = models.JSONField(default=dict, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.export_format} — {self.created_at}"


class BaseKpiDefinition(models.Model):
    """Abstract base for KPI definitions."""

    CATEGORIES = [
        ("hr", "Ressources Humaines"),
        ("finance", "Finance"),
        ("benefits", "Prestations"),
        ("conventions", "Conventions"),
        ("global", "Global"),
    ]
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    unit = models.CharField(max_length=50, blank=True)
    target_value = models.FloatField(null=True, blank=True)
    formula = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        ordering = ["category", "display_order", "name"]

    def __str__(self):
        return f"[{self.category}] {self.name} ({self.code})"


class BaseKpiSnapshot(models.Model):
    """Abstract base for KPI snapshots."""

    value = models.FloatField()
    date = models.DateField()
    previous_value = models.FloatField(null=True, blank=True)
    variation = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        ordering = ["-date"]
        unique_together = [("kpi", "date")]


class BaseDashboardWidget(models.Model):
    """Abstract base for dashboard widgets."""

    WIDGET_TYPES = [
        ("kpi_summary", "Résumé KPI"),
        ("kpi_card", "Carte KPI"),
        ("chart_bar", "Barres"),
        ("chart_line", "Courbes"),
        ("chart_pie", "Camembert"),
        ("table", "Tableau"),
        ("alert_feed", "Flux d'alertes"),
        ("stat_card", "Carte statistique"),
        ("custom", "Personnalisé"),
    ]
    SIZES = [
        ("sm", "Petit"),
        ("md", "Moyen"),
        ("lg", "Grand"),
        ("xl", "Très grand"),
        ("full", "Plein largeur"),
    ]
    title = models.CharField(max_length=200)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    size = models.CharField(max_length=10, choices=SIZES, default="md")
    config = models.JSONField(default=dict, blank=True)
    is_global = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.get_widget_type_display()} — {self.title}"
