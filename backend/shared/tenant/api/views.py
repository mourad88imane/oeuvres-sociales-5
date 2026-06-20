from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsAdmin
from shared.tenant.models import Tenant

from .serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    search_fields = ["name", "slug", "domain"]
    ordering_fields = ["name", "created_at"]
