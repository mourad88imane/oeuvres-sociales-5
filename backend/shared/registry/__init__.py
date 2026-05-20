"""Engine Registry — plugin system for registering business models with shared engines."""
import logging
from collections import defaultdict

logger = logging.getLogger("shared.registry")


class EngineRegistry:
    """
    Central registry for connecting generic engines to business models.
    
    Usage in apps.ready():
        from shared.registry import registry
        registry.register_audit_models("myapp.MyModel")
        registry.register_workflow_models("myapp.MyModel", workflow_definition=MyWorkflow)
        
    Then engines look up:
        registry.get_audit_models() -> ["myapp.MyModel", ...]
    """

    def __init__(self):
        self._audit_models: set[str] = set()
        self._workflow_models: dict[str, object] = {}
        self._notification_handlers: dict[str, list[callable]] = defaultdict(list)
        self._report_handlers: dict[str, list[callable]] = defaultdict(list)
        self._permission_roles: set[str] = set()
        self._metric_providers: list[callable] = []

    # ── Audit ─────────────────────────────────────────────
    def register_audit_models(self, *model_paths: str):
        """Register model paths (e.g. 'employees.Employee') to be auto-audited."""
        self._audit_models.update(model_paths)

    def get_audit_models(self) -> set[str]:
        return self._audit_models

    # ── Workflow ──────────────────────────────────────────
    def register_workflow_model(self, model_path: str, workflow_definition):
        """Register a model with its workflow definition."""
        self._workflow_models[model_path] = workflow_definition

    def get_workflow_definition(self, model_path: str):
        return self._workflow_models.get(model_path)

    def get_all_workflow_models(self) -> dict[str, object]:
        return dict(self._workflow_models)

    # ── Notifications ─────────────────────────────────────
    def register_notification_handler(self, event_type: str, handler: callable):
        self._notification_handlers[event_type].append(handler)

    def get_notification_handlers(self, event_type: str) -> list[callable]:
        return self._notification_handlers.get(event_type, [])

    # ── Reports ───────────────────────────────────────────
    def register_report_handler(self, report_code: str, handler: callable):
        self._report_handlers[report_code].append(handler)

    def get_report_handlers(self, report_code: str) -> list[callable]:
        return self._report_handlers.get(report_code, [])

    # ── Permissions ───────────────────────────────────────
    def register_role(self, role: str):
        self._permission_roles.add(role)

    def get_roles(self) -> set[str]:
        return self._permission_roles

    def has_role(self, role: str) -> bool:
        return role in self._permission_roles

    # ── Metrics ───────────────────────────────────────────
    def register_metric_provider(self, provider: callable):
        self._metric_providers.append(provider)

    def get_metric_providers(self) -> list[callable]:
        return list(self._metric_providers)

    # ── Bulk registration ─────────────────────────────────
    def configure_from_settings(self, settings_obj):
        """Load configuration from Django settings."""
        audit_models = getattr(settings_obj, "ENGINE_AUDIT_MODELS", None)
        if audit_models:
            self.register_audit_models(*audit_models)

        roles = getattr(settings_obj, "ENGINE_ROLES", None)
        if roles:
            for role in roles:
                self.register_role(role)


registry = EngineRegistry()
