from core.models import BaseModel
from django.conf import settings
from django.db import models


class KpiDefinition(BaseModel):
    CATEGORIES = [
        ("hr", "Ressources Humaines"),
        ("finance", "Finance"),
        ("benefits", "Prestations"),
        ("conventions", "Conventions"),
        ("global", "Global"),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    category = models.CharField(max_length=20, choices=CATEGORIES, verbose_name="Catégorie")
    unit = models.CharField(max_length=50, blank=True, verbose_name="Unité")
    target_value = models.FloatField(null=True, blank=True, verbose_name="Valeur cible")
    formula = models.TextField(blank=True, verbose_name="Formule de calcul")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")

    class Meta:
        verbose_name = "Indicateur KPI"
        verbose_name_plural = "Indicateurs KPI"
        ordering = ["category", "display_order", "name"]

    def __str__(self):
        return f"[{self.category}] {self.name} ({self.code})"


class KpiSnapshot(BaseModel):
    kpi = models.ForeignKey(
        KpiDefinition, on_delete=models.CASCADE, related_name="snapshots", verbose_name="KPI"
    )
    value = models.FloatField(verbose_name="Valeur")
    date = models.DateField(verbose_name="Date du snapshot")
    previous_value = models.FloatField(null=True, blank=True, verbose_name="Valeur précédente")
    variation = models.FloatField(null=True, blank=True, verbose_name="Variation (%)")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")

    class Meta:
        verbose_name = "Snapshot KPI"
        verbose_name_plural = "Snapshots KPI"
        ordering = ["-date", "kpi"]
        unique_together = [("kpi", "date")]
        indexes = [
            models.Index(fields=["kpi", "-date"]),
        ]

    def __str__(self):
        return f"{self.kpi.code} = {self.value} ({self.date})"


class DashboardWidget(BaseModel):
    WIDGET_TYPES = [
        ("kpi_summary", "Résumé KPI"),
        ("kpi_card", "Carte KPI"),
        ("chart_bar", "Barres"),
        ("chart_line", "Courbes"),
        ("chart_pie", "Camembert"),
        ("chart_donut", "Donut"),
        ("table", "Tableau"),
        ("list", "Liste"),
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="dashboard_widgets",
        verbose_name="Utilisateur",
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, verbose_name="Type")
    size = models.CharField(max_length=10, choices=SIZES, default="md", verbose_name="Taille")
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuration")
    is_global = models.BooleanField(default=False, verbose_name="Global")
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Widget tableau de bord"
        verbose_name_plural = "Widgets tableau de bord"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.get_widget_type_display()} — {self.title}"


class ReportDefinition(BaseModel):
    FORMATS = [
        ("excel", "Excel"),
        ("csv", "CSV"),
        ("pdf", "PDF"),
        ("json", "JSON"),
    ]

    CATEGORIES = [
        ("employees", "Employés"),
        ("benefits", "Prestations"),
        ("finance", "Finance"),
        ("conventions", "Conventions"),
        ("kpi", "Indicateurs KPI"),
        ("custom", "Personnalisé"),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    category = models.CharField(max_length=20, choices=CATEGORIES, verbose_name="Catégorie")
    default_format = models.CharField(
        max_length=10, choices=FORMATS, default="excel", verbose_name="Format par défaut"
    )
    filters_config = models.JSONField(
        default=dict, blank=True, verbose_name="Configuration des filtres"
    )
    columns_config = models.JSONField(
        default=list, blank=True, verbose_name="Configuration des colonnes"
    )
    chart_config = models.JSONField(
        default=dict, blank=True, verbose_name="Configuration graphique"
    )
    is_system = models.BooleanField(default=False, verbose_name="Rapport système")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    ai_insights_enabled = models.BooleanField(default=False, verbose_name="Insights IA")

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ["category", "title"]

    def __str__(self):
        return f"{self.title} ({self.code})"


class ReportSchedule(BaseModel):
    FREQUENCIES = [
        ("daily", "Quotidien"),
        ("weekly", "Hebdomadaire"),
        ("monthly", "Mensuel"),
        ("quarterly", "Trimestriel"),
        ("yearly", "Annuel"),
        ("custom", "Personnalisé"),
    ]

    report = models.ForeignKey(
        ReportDefinition, on_delete=models.CASCADE, related_name="schedules", verbose_name="Rapport"
    )
    frequency = models.CharField(max_length=15, choices=FREQUENCIES, verbose_name="Fréquence")
    cron_expression = models.CharField(max_length=100, blank=True, verbose_name="Expression cron")
    recipients = models.JSONField(default=list, blank=True, verbose_name="Destinataires")
    format = models.CharField(
        max_length=10, choices=ReportDefinition.FORMATS, default="excel", verbose_name="Format"
    )
    export_format = models.CharField(
        max_length=10,
        choices=ReportDefinition.FORMATS,
        default="excel",
        verbose_name="Format d'export",
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="Dernière exécution")
    next_run = models.DateTimeField(null=True, blank=True, verbose_name="Prochaine exécution")
    filters_override = models.JSONField(
        default=dict, blank=True, verbose_name="Filtres personnalisés"
    )

    class Meta:
        verbose_name = "Planification rapport"
        verbose_name_plural = "Planifications rapports"
        ordering = ["next_run"]

    def __str__(self):
        return f"{self.report.title} — {self.get_frequency_display()}"


class DataExport(BaseModel):
    STATUSES = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échoué"),
    ]

    report = models.ForeignKey(
        ReportDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exports",
        verbose_name="Rapport",
    )
    export_format = models.CharField(
        max_length=10, choices=ReportDefinition.FORMATS, verbose_name="Format"
    )
    file = models.FileField(
        upload_to="exports/%Y/%m/", null=True, blank=True, verbose_name="Fichier"
    )
    file_size = models.PositiveIntegerField(default=0, verbose_name="Taille (octets)")
    status = models.CharField(
        max_length=15, choices=STATUSES, default="pending", verbose_name="Statut"
    )
    filters_used = models.JSONField(default=dict, blank=True, verbose_name="Filtres utilisés")
    row_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de lignes")
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Terminé le")
    duration_ms = models.PositiveIntegerField(default=0, verbose_name="Durée (ms)")

    class Meta:
        verbose_name = "Export de données"
        verbose_name_plural = "Exports de données"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_export_format_display()} — {self.created_at.date()}"
