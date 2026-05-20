"""
============================================================
DEPARTMENT SERIALIZERS
============================================================
"""
from rest_framework import serializers
from core.serializers import BaseModelSerializer
from .models import Department


class DepartmentListSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour les listes déroulantes et références."""
    employee_count = serializers.ReadOnlyField()
    full_path      = serializers.ReadOnlyField()

    class Meta:
        model  = Department
        fields = ["id", "code", "name", "full_path",
                  "employee_count", "is_active"]


class DepartmentSerializer(BaseModelSerializer):
    """Sérialiseur complet."""
    employee_count   = serializers.ReadOnlyField()
    full_path        = serializers.ReadOnlyField()
    parent_name      = serializers.CharField(
        source="parent.name", read_only=True, default=None
    )
    manager_name     = serializers.SerializerMethodField()
    children_count   = serializers.SerializerMethodField()

    class Meta:
        model  = Department
        fields = [
            "id", "code", "name", "description",
            "parent", "parent_name", "full_path",
            "manager", "manager_name",
            "is_active", "budget_annual", "cost_center", "location",
            "employee_count", "children_count",
            "created_at", "updated_at", "created_by_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name()
        return None

    def get_children_count(self, obj):
        return obj.children.filter(is_deleted=False).count()

    def validate_code(self, value):
        return value.upper().strip()

    def validate(self, attrs):
        # Éviter la récursion infinie dans la hiérarchie
        parent = attrs.get("parent")
        if parent and self.instance and parent.pk == self.instance.pk:
            raise serializers.ValidationError(
                {"parent": "Un département ne peut pas être son propre parent."}
            )
        return attrs


class DepartmentCreateSerializer(BaseModelSerializer):
    class Meta:
        model  = Department
        fields = ["code", "name", "description", "parent",
                  "manager", "is_active", "budget_annual",
                  "cost_center", "location"]

    def validate_code(self, value):
        return value.upper().strip()
