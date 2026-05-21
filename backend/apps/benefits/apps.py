from django.apps import AppConfig


class BenefitsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.benefits"
    verbose_name = "Prestations"

    def ready(self):
        # Register workflow definition with engine registry
        try:
            from shared.registry import registry

            from .workflow import BenefitWorkflow

            registry.register_workflow_model("apps.benefits.Benefit", BenefitWorkflow)
        except ImportError:
            pass
        # Wire AI signals
        try:
            from .signals import wire_benefit_signals

            wire_benefit_signals()
        except ImportError:
            pass
