from django.urls import include, path
from rest_framework.routers import DefaultRouter

from shared.workflow.api.views import (
    WorkflowModelListView,
    WorkflowStateViewSet,
    WorkflowTransitionViewSet,
)

from .views import (
    ApprovalHistoryViewSet,
    ApprovalMatrixViewSet,
    PermissionViewSet,
    RolePermissionViewSet,
    RoleViewSet,
    SystemParameterViewSet,
    UserRoleAssignmentViewSet,
    WorkflowPermissionViewSet,
)

app_name = "administration"

router = DefaultRouter()
router.register(r"system-parameters", SystemParameterViewSet, basename="system-parameter")
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"role-permissions", RolePermissionViewSet, basename="role-permission")
router.register(r"user-roles", UserRoleAssignmentViewSet, basename="user-role")
router.register(r"workflow-permissions", WorkflowPermissionViewSet, basename="workflow-permission")
router.register(r"approval-matrix", ApprovalMatrixViewSet, basename="approval-matrix")
router.register(r"approval-history", ApprovalHistoryViewSet, basename="approval-history")
# Dynamic workflow designer
router.register(r"workflow-states", WorkflowStateViewSet, basename="workflow-state")
router.register(r"workflow-transitions", WorkflowTransitionViewSet, basename="workflow-transition")
router.register(r"workflow-models", WorkflowModelListView, basename="workflow-model")

urlpatterns = [
    path("", include(router.urls)),
]
