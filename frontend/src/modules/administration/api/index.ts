import apiClient from "@shared/api/apiClient";

// ── System Parameters ─────────────────────────────────

export const fetchSystemParameters = () =>
  apiClient.get("/admin/system-parameters/").then((r) => r.data);

export const fetchSystemParameterByKey = (key: string) =>
  apiClient.get(`/admin/system-parameters/by-key/${key}/`).then((r) => r.data?.data);

export const updateSystemParameter = (id: string, data: { value: string }) =>
  apiClient.patch(`/admin/system-parameters/${id}/`, data).then((r) => r.data?.data);

export const updateSystemParameterByKey = (key: string, data: { value: string }) =>
  apiClient.patch(`/admin/system-parameters/by-key/${key}/`, data).then((r) => r.data?.data);

// ── Roles ─────────────────────────────────────────────

export const fetchRoles = (params?: Record<string, any>) =>
  apiClient.get("/admin/roles/", { params }).then((r) => r.data);

export const fetchRole = (id: string) =>
  apiClient.get(`/admin/roles/${id}/`).then((r) => r.data);

export const createRole = (data: Record<string, any>) =>
  apiClient.post("/admin/roles/", data).then((r) => r.data);

export const updateRole = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/admin/roles/${id}/`, data).then((r) => r.data);

export const deleteRole = (id: string) =>
  apiClient.delete(`/admin/roles/${id}/`).then((r) => r.data);

// ── Permissions ───────────────────────────────────────

export const fetchPermissions = (params?: Record<string, any>) =>
  apiClient.get("/admin/permissions/", { params }).then((r) => r.data);

export const fetchPermission = (id: string) =>
  apiClient.get(`/admin/permissions/${id}/`).then((r) => r.data);

export const createPermission = (data: Record<string, any>) =>
  apiClient.post("/admin/permissions/", data).then((r) => r.data);

export const updatePermission = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/admin/permissions/${id}/`, data).then((r) => r.data);

export const deletePermission = (id: string) =>
  apiClient.delete(`/admin/permissions/${id}/`).then((r) => r.data);

// ── Role Permissions ──────────────────────────────────

export const fetchRolePermissions = (params?: Record<string, any>) =>
  apiClient.get("/admin/role-permissions/", { params }).then((r) => r.data);

export const assignPermissionToRole = (role: string, permission: string) =>
  apiClient.post("/admin/role-permissions/", { role, permission }).then((r) => r.data);

export const removePermissionFromRole = (id: string) =>
  apiClient.delete(`/admin/role-permissions/${id}/`).then((r) => r.data);

// ── User Role Assignments ─────────────────────────────

export const fetchUserRoleAssignments = (params?: Record<string, any>) =>
  apiClient.get("/admin/user-roles/", { params }).then((r) => r.data);

export const assignRoleToUser = (data: Record<string, any>) =>
  apiClient.post("/admin/user-roles/", data).then((r) => r.data);

export const removeUserRoleAssignment = (id: string) =>
  apiClient.delete(`/admin/user-roles/${id}/`).then((r) => r.data);

// ── Workflow Permissions ──────────────────────────────

export const fetchWorkflowPermissions = (params?: Record<string, any>) =>
  apiClient.get("/admin/workflow-permissions/", { params }).then((r) => r.data);

export const createWorkflowPermission = (data: Record<string, any>) =>
  apiClient.post("/admin/workflow-permissions/", data).then((r) => r.data);

export const deleteWorkflowPermission = (id: string) =>
  apiClient.delete(`/admin/workflow-permissions/${id}/`).then((r) => r.data);

// ── Approval Matrix ───────────────────────────────────

export const fetchApprovalMatrix = (params?: Record<string, any>) =>
  apiClient.get("/admin/approval-matrix/", { params }).then((r) => r.data);

export const createApprovalMatrixEntry = (data: Record<string, any>) =>
  apiClient.post("/admin/approval-matrix/", data).then((r) => r.data);

export const updateApprovalMatrixEntry = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/admin/approval-matrix/${id}/`, data).then((r) => r.data);

export const deleteApprovalMatrixEntry = (id: string) =>
  apiClient.delete(`/admin/approval-matrix/${id}/`).then((r) => r.data);

// ── Workflow Designer ───────────────────────────────

export const fetchWorkflowModels = () =>
  apiClient.get("/admin/workflow-models/").then((r) => r.data);

export const fetchWorkflowStates = (params?: Record<string, any>) =>
  apiClient.get("/admin/workflow-states/", { params }).then((r) => r.data);

export const createWorkflowState = (data: Record<string, any>) =>
  apiClient.post("/admin/workflow-states/", data).then((r) => r.data);

export const updateWorkflowState = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/admin/workflow-states/${id}/`, data).then((r) => r.data);

export const deleteWorkflowState = (id: string) =>
  apiClient.delete(`/admin/workflow-states/${id}/`).then((r) => r.data);

export const fetchWorkflowTransitions = (params?: Record<string, any>) =>
  apiClient.get("/admin/workflow-transitions/", { params }).then((r) => r.data);

export const createWorkflowTransition = (data: Record<string, any>) =>
  apiClient.post("/admin/workflow-transitions/", data).then((r) => r.data);

export const updateWorkflowTransition = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/admin/workflow-transitions/${id}/`, data).then((r) => r.data);

export const deleteWorkflowTransition = (id: string) =>
  apiClient.delete(`/admin/workflow-transitions/${id}/`).then((r) => r.data);

export const addRoleToTransition = (transitionId: string, role: string) =>
  apiClient.post(`/admin/workflow-transitions/${transitionId}/add_role/`, { role }).then((r) => r.data);

export const removeRoleFromTransition = (transitionId: string, roleSlug: string) =>
  apiClient.post(`/admin/workflow-transitions/${transitionId}/remove_role/`, { role_slug: roleSlug }).then((r) => r.data);

// ── Approval History ──────────────────────────────────

export const fetchApprovalHistory = (params?: Record<string, any>) =>
  apiClient.get("/admin/approval-history/", { params }).then((r) => r.data);
