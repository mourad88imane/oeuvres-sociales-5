from rest_framework import serializers

from shared.tenant.models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id", "name", "slug", "domain", "logo", "is_active",
            "max_users", "config", "features", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
