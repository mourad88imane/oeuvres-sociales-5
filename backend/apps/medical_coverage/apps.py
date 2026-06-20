from django.apps import AppConfig


class MedicalCoverageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.medical_coverage"
    verbose_name = "Couverture Médicale"

    def ready(self):
        from shared.registry import registry
        registry.register_workflow_model(
            "apps.medical_coverage.MedicalCoverageVoucher",
            "apps.medical_coverage.workflow.MedicalCoverageWorkflow",
        )
        import apps.medical_coverage.signals  # noqa
