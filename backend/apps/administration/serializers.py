from rest_framework import serializers

from .models import (
    ApprovalHistory,
    ApprovalMatrix,
    Permission,
    Role,
    RolePermission,
    SystemParameter,
    UserRoleAssignment,
    WorkflowPermission,
)

# =========================================================================
# SYSTEM PARAMETERS
# =========================================================================


class SystemParameterSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SystemParameter
        fields = [
            "id", "key", "value", "description",
            "updated_by", "updated_by_name",
            "updated_at", "created_at",
        ]
        read_only_fields = ["id", "updated_by", "updated_by_name", "updated_at", "created_at"]

    def get_updated_by_name(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None


# =========================================================================
# ROLES
# =========================================================================


class RoleSerializer(serializers.ModelSerializer):
    permission_count = serializers.IntegerField(read_only=True, default=0)
    user_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Role
        fields = [
            "id", "name", "slug", "description",
            "is_system", "is_active", "rank",
            "permission_count", "user_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


# =========================================================================
# PERMISSIONS
# =========================================================================


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id", "codename", "name", "description", "module",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# =========================================================================
# ROLE PERMISSION
# =========================================================================


class RolePermissionSerializer(serializers.ModelSerializer):
    role_slug = serializers.CharField(source="role.slug", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    permission_codename = serializers.CharField(source="permission.codename", read_only=True)
    permission_name = serializers.CharField(source="permission.name", read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            "id", "role", "role_slug", "role_name",
            "permission", "permission_codename", "permission_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# =========================================================================
# USER ROLE ASSIGNMENT
# =========================================================================


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    role_slug = serializers.CharField(source="role.slug", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    assigned_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserRoleAssignment
        fields = [
            "id", "user", "user_email", "user_name",
            "role", "role_slug", "role_name",
            "assigned_by", "assigned_by_name",
            "expires_at", "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "assigned_by", "created_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_assigned_by_name(self, obj):
        return obj.assigned_by.get_full_name() if obj.assigned_by else None


# =========================================================================
# WORKFLOW PERMISSION
# =========================================================================


class WorkflowPermissionSerializer(serializers.ModelSerializer):
    role_slug = serializers.CharField(source="role.slug", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    permission_codename = serializers.CharField(
        source="permission.codename", read_only=True, allow_null=True
    )
    permission_name = serializers.CharField(
        source="permission.name", read_only=True, allow_null=True
    )

    class Meta:
        model = WorkflowPermission
        fields = [
            "id", "app_label", "model_name",
            "from_state", "to_state",
            "role", "role_slug", "role_name",
            "permission", "permission_codename", "permission_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# =========================================================================
# APPROVAL MATRIX
# =========================================================================


class ApprovalMatrixSerializer(serializers.ModelSerializer):
    required_roles = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Role.objects.all()
    )
    required_role_names = serializers.SerializerMethodField(read_only=True)
    required_role_slugs = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApprovalMatrix
        fields = [
            "id", "module", "min_amount", "max_amount",
            "approval_level", "required_roles",
            "required_role_names", "required_role_slugs",
            "is_active", "description",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_required_role_names(self, obj):
        return [r.name for r in obj.required_roles.all()]

    def get_required_role_slugs(self, obj):
        return [r.slug for r in obj.required_roles.all()]


# =========================================================================
# APPROVAL HISTORY
# =========================================================================


class ApprovalHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    content_type_name = serializers.SerializerMethodField(read_only=True)
    object_str = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApprovalHistory
        fields = [
            "id", "content_type", "content_type_name",
            "object_id", "object_str",
            "action", "action_display",
            "user", "user_name", "date", "comment", "from_state", "to_state",
        ]
        read_only_fields = ["id", "date"]

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else None

    def get_content_type_name(self, obj):
        return obj.content_type.model if obj.content_type else None

    def get_object_str(self, obj):
        return str(obj.content_object) if obj.content_object else None
