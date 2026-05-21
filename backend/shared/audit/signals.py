import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

logger = logging.getLogger("audit")

EXCLUDE_FIELDS = {"password", "last_login", "is_superuser", "user_permissions", "groups"}


def get_audit_model_set():
    """Get audited models from registry or fallback to settings."""
    try:
        from shared.registry import registry

        models = registry.get_audit_models()
        if models:
            return models
    except ImportError:
        pass
    # Fallback : configuration Django
    from django.conf import settings

    return set(getattr(settings, "ENGINE_AUDIT_MODELS", []))


def should_audit(sender):
    model_path = f"{sender._meta.app_label}.{sender.__name__}"
    return model_path in get_audit_model_set()


def get_user(request=None):
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    return None


try:

    @receiver(post_save)
    def audit_model_create_update(sender, instance, created, **kwargs):
        if not should_audit(sender):
            return
        try:
            from .services import AuditService

            update_fields = kwargs.get("update_fields")
            if update_fields and len(update_fields) == 1 and "updated_at" in update_fields:
                return

            request = getattr(instance, "_request", None)
            user = getattr(instance, "_user", None) or get_user(request)
            audit = AuditService()

            if created:
                audit.log_create(user=user, obj=instance, request=request)
            else:
                try:
                    before = model_to_dict(instance, exclude=EXCLUDE_FIELDS)
                    history = instance.history.all()
                    if history.exists() and history.first().prev_record:
                        before = model_to_dict(
                            history.first().prev_record.instance, exclude=EXCLUDE_FIELDS
                        )
                except Exception:
                    before = {}
                audit.log_update(user=user, obj=instance, before_data=before, request=request)
        except Exception as e:
            logger.error("Auto audit post_save failed: %s", e, exc_info=True)

    @receiver(post_delete)
    def audit_model_delete(sender, instance, **kwargs):
        if not should_audit(sender):
            return
        try:
            from .services import AuditService

            request = getattr(instance, "_request", None)
            user = getattr(instance, "_user", None) or get_user(request)
            audit = AuditService()
            audit.log_delete(user=user, obj=instance, request=request)
        except Exception as e:
            logger.error("Auto audit post_delete failed: %s", e, exc_info=True)

except ImportError:
    logger.warning("simple_history not available, audit signals disabled")
