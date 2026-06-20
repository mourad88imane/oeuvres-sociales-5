from django.apps import AppConfig


class LoansConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.loans"
    verbose_name = "Prêts"

    def ready(self):
        try:
            from shared.registry import registry
            from .workflow import LoanWorkflow
            registry.register_workflow_model("apps.loans.Loan", LoanWorkflow)
        except ImportError:
            pass
