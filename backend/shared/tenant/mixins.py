from rest_framework import serializers


class TenantViewSetMixin:
    """Mixin for ModelViewSets that scopes queries to the current tenant.

    Overrides ``filter_queryset()`` (post-get_queryset hook) so tenant
    filtering applies even to viewsets that override ``get_queryset()``.

    Also overrides ``perform_create()`` to auto-assign the tenant.

    Skips filtering when the user is superadmin or no tenant is set.
    """

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        tenant = getattr(self.request, "tenant", None)
        user = getattr(self.request, "user", None)
        if tenant is not None and not (user and user.is_superuser):
            model = getattr(queryset, "model", None)
            if model is not None and hasattr(model, "tenant"):
                return queryset.filter(tenant=tenant)
        return queryset

    def perform_create(self, serializer):
        tenant = getattr(self.request, "tenant", None)
        if tenant is not None and hasattr(serializer.Meta.model, "tenant"):
            serializer.save(tenant=tenant)
        else:
            serializer.save()
