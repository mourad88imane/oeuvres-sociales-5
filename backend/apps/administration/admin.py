from django.contrib import admin

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


@admin.register(SystemParameter)
class SystemParameterAdmin(admin.ModelAdmin):
    list_display = ["key", "value", "description", "updated_at"]
    search_fields = ["key", "description"]
    readonly_fields = ["updated_at", "created_at"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_system", "is_active", "rank"]
    list_filter = ["is_system", "is_active"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["codename", "name", "module"]
    list_filter = ["module"]
    search_fields = ["codename", "name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission"]
    list_filter = ["role", "permission__module"]
    search_fields = ["role__name", "permission__codename"]


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "assigned_by", "is_active", "expires_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "role__name"]
    readonly_fields = ["created_at"]


@admin.register(WorkflowPermission)
class WorkflowPermissionAdmin(admin.ModelAdmin):
    list_display = ["app_label", "model_name", "from_state", "to_state", "role"]
    list_filter = ["app_label", "model_name", "role"]
    search_fields = ["app_label", "model_name"]


@admin.register(ApprovalMatrix)
class ApprovalMatrixAdmin(admin.ModelAdmin):
    list_display = ["module", "approval_level", "min_amount", "max_amount", "is_active"]
    list_filter = ["module", "is_active", "approval_level"]


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ["object_id", "content_type", "action", "user", "date"]
    list_filter = ["action", "date", "content_type"]
    search_fields = ["object_id", "comment"]
    readonly_fields = ["date"]
