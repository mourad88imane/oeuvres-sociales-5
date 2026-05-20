"""API mixins — réutilisables dans tous les projets."""
from shared.audit.services import AuditService


class AuditMixin:
    """
    Mixin qui journalise automatiquement les actions CRUD via AuditService.
    
    Usage:
        class MyViewSet(AuditMixin, GenericModelViewSet):
            ...
    """
    audit_service = AuditService()

    def perform_create(self, serializer):
        instance = serializer.save()
        self.audit_service.log_create(
            user=self.request.user,
            obj=instance,
            request=self.request,
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        from django.forms.models import model_to_dict
        before = model_to_dict(instance)
        instance = serializer.save()
        self.audit_service.log_update(
            user=self.request.user,
            obj=instance,
            before_data=before,
            request=self.request,
        )

    def perform_destroy(self, instance):
        self.audit_service.log_delete(
            user=self.request.user,
            obj=instance,
            request=self.request,
        )
        instance.soft_delete(self.request.user) if hasattr(instance, "soft_delete") else instance.delete()
