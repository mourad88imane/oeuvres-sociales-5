from django.apps import AppConfig


class ReportingEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared.reporting"
    label = "shared_reporting"
    verbose_name = "Moteur de reporting"
