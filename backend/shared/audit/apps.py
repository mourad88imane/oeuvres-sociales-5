from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared.audit"
    verbose_name = "Audit Trail"

    def ready(self):
        # Register audit signal handlers
        import shared.audit.signals  # noqa: F401

        # Load audit model configuration
        try:
            from django.conf import settings
            from shared.registry import registry

            configured_models = getattr(settings, "ENGINE_AUDIT_MODELS", [])
            if configured_models:
                registry.register_audit_models(*configured_models)
        except ImportError:
            pass
