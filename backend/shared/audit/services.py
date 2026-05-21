"""
============================================================
AUDIT SERVICE — Service de création des logs d'audit
============================================================
Usage dans les vues et services :
    from shared.audit.services import AuditService
    audit = AuditService()
    audit.log_action(user=request.user, action="CREATE", obj=instance)
"""

import logging

from django.forms.models import model_to_dict

from .models import AuditLog

logger = logging.getLogger("audit")


class AuditService:
    """
    Service centralisé pour la création des logs d'audit.
    Toutes les actions importantes passent par ce service.
    """

    def log_action(
        self,
        action: str,
        user=None,
        obj=None,
        before_data: dict = None,
        after_data: dict = None,
        extra_data: dict = None,
        request=None,
        severity: str = AuditLog.Severity.LOW,
    ) -> AuditLog:
        """Créé un log d'audit générique."""
        try:
            log_data = {
                "action": action,
                "severity": severity,
                "extra_data": extra_data or {},
            }

            # Contexte utilisateur
            if user and not user.is_anonymous:
                log_data["user"] = user
                log_data["user_email"] = user.email
                log_data["user_role"] = user.role

            # Contexte requête HTTP
            if request:
                log_data["ip_address"] = self._get_ip(request)
                log_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")[:500]
                log_data["endpoint"] = request.path[:500]
                log_data["http_method"] = request.method
                log_data["request_id"] = request.META.get("HTTP_X_REQUEST_ID", "")[:100]

            # Contexte objet
            if obj is not None:
                log_data["content_type_name"] = f"{obj._meta.app_label}.{obj._meta.model_name}"
                log_data["object_id"] = str(obj.pk)
                log_data["object_repr"] = str(obj)[:500]

            # Données avant/après
            if before_data is not None:
                log_data["before_data"] = self._serialize_data(before_data)
            if after_data is not None:
                log_data["after_data"] = self._serialize_data(after_data)

            # Calcul des champs modifiés
            if before_data and after_data:
                log_data["changed_fields"] = self._get_changed_fields(before_data, after_data)

            entry = AuditLog(**log_data)
            entry.save()

            # Log structuré pour les systèmes d'analyse (ELK, etc.)
            logger.info(
                "Audit event",
                extra={
                    "audit_action": action,
                    "audit_user": log_data.get("user_email", "anonymous"),
                    "audit_object": log_data.get("content_type_name", ""),
                    "audit_object_id": log_data.get("object_id", ""),
                    "audit_severity": severity,
                },
            )

            return entry

        except Exception as e:
            # Ne jamais faire planter l'app à cause d'un log d'audit
            logger.error(f"Audit log creation failed: {e}", exc_info=True)
            return None

    def log_create(self, user, obj, request=None, **kwargs):
        return self.log_action(
            action=AuditLog.Action.CREATE,
            user=user,
            obj=obj,
            request=request,
            after_data=self._obj_to_dict(obj),
            **kwargs,
        )

    def log_update(self, user, obj, before_data: dict, request=None, **kwargs):
        return self.log_action(
            action=AuditLog.Action.UPDATE,
            user=user,
            obj=obj,
            request=request,
            before_data=before_data,
            after_data=self._obj_to_dict(obj),
            severity=AuditLog.Severity.MEDIUM,
            **kwargs,
        )

    def log_delete(self, user, obj, request=None, **kwargs):
        return self.log_action(
            action=AuditLog.Action.DELETE,
            user=user,
            obj=obj,
            request=request,
            before_data=self._obj_to_dict(obj),
            severity=AuditLog.Severity.HIGH,
            **kwargs,
        )

    def log_login(self, user, ip: str, success: bool = True):
        action = AuditLog.Action.LOGIN if success else AuditLog.Action.LOGIN_FAILED
        severity = AuditLog.Severity.LOW if success else AuditLog.Severity.MEDIUM
        return self.log_action(
            action=action,
            user=user,
            severity=severity,
            extra_data={"ip": ip, "success": success},
        )

    def log_logout(self, user):
        return self.log_action(action=AuditLog.Action.LOGOUT, user=user)

    def log_workflow_transition(self, user, obj, from_state: str, to_state: str, request=None):
        return self.log_action(
            action=AuditLog.Action.WORKFLOW_TRANSITION,
            user=user,
            obj=obj,
            request=request,
            severity=AuditLog.Severity.MEDIUM,
            extra_data={"from_state": from_state, "to_state": to_state},
        )

    def log_export(self, user, content_type: str, filters: dict = None, request=None):
        return self.log_action(
            action=AuditLog.Action.EXPORT,
            user=user,
            request=request,
            severity=AuditLog.Severity.MEDIUM,
            extra_data={"content_type": content_type, "filters": filters or {}},
        )

    # ── Helpers privés ───────────────────────────────────
    def _get_ip(self, request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _obj_to_dict(self, obj) -> dict:
        """Convertit un objet Django en dict sérialisable."""
        try:
            return model_to_dict(obj, exclude=["password"])
        except Exception:
            return {"repr": str(obj)}

    def _serialize_data(self, data: dict) -> dict:
        """Sérialise les données pour le stockage JSON."""
        result = {}
        for key, value in data.items():
            try:
                import json

                json.dumps(value)  # Test de sérialisation
                result[key] = value
            except (TypeError, ValueError):
                result[key] = str(value)
        return result

    def _get_changed_fields(self, before: dict, after: dict) -> list:
        """Retourne la liste des champs qui ont changé."""
        changed = []
        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            if before.get(key) != after.get(key):
                changed.append(key)
        return changed
