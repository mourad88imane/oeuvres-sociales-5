from django.db import models


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)


class TenantManager(models.Manager):
    """Manager that scopes queries to the current tenant.

    Usage in views:
        Model.objects.for_tenant(request.tenant).filter(...)

    The manager also provides ``all()`` unfiltered for admin/superadmin use.
    """

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)
