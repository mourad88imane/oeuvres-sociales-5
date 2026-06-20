import re

from django.utils.deprecation import MiddlewareMixin

from shared.tenant.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """Extracts the current tenant from the request.

    Resolution order:
      1. `X-Tenant-ID` header (superadmin override)
      2. JWT claim `tenant_id` (decoded by DRF, stored on `request.auth`)
      3. Subdomain match against `Tenant.domain`
      4. First active tenant (fallback for single-tenant setups)
    """

    def process_request(self, request):
        tenant = None

        # 1. Header override (superadmin impersonation)
        header_id = request.META.get("HTTP_X_TENANT_ID")
        if header_id:
            try:
                tenant = Tenant.objects.get(id=header_id, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                pass

        # 2. JWT claim
        if tenant is None and hasattr(request, "auth") and request.auth is not None:
            try:
                payload = request.auth.payload if hasattr(request.auth, "payload") else {}
                tid = payload.get("tenant_id")
                if tid:
                    tenant = Tenant.objects.get(id=tid, is_active=True)
            except (Tenant.DoesNotExist, Exception):
                pass

        # 3. Subdomain
        if tenant is None:
            host = request.get_host().split(":")[0]
            try:
                tenant = Tenant.objects.get(domain=host, is_active=True)
            except Tenant.DoesNotExist:
                pass

        # 4. Single-tenant fallback
        if tenant is None:
            tenant = Tenant.objects.filter(is_active=True).first()

        request.tenant = tenant
