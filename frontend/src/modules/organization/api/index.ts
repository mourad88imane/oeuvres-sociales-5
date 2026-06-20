import apiClient from "@shared/api/apiClient";

export interface DirectionItem {
  id: string;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  ordering: number;
  sub_directions_count: number;
  created_at: string;
  updated_at: string;
}

export interface SubDirectionItem {
  id: string;
  direction: string;
  direction_name: string;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  ordering: number;
  services_count: number;
  created_at: string;
  updated_at: string;
}

export interface ServiceItem {
  id: string;
  sub_direction: string;
  sub_direction_name: string;
  direction_id: string;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  ordering: number;
  bureaux_count: number;
  created_at: string;
  updated_at: string;
}

export interface BureauItem {
  id: string;
  service: string;
  service_name: string;
  sub_direction_id: string;
  direction_id: string;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  ordering: number;
  created_at: string;
  updated_at: string;
}

export interface FunctionItem {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  ordering: number;
  created_at: string;
  updated_at: string;
}

export interface GradeItem {
  id: string;
  name: string;
  level: number;
  description: string;
  is_active: boolean;
  ordering: number;
  created_at: string;
  updated_at: string;
}

export interface OrganizationLookup {
  directions: DirectionItem[];
  sub_directions: SubDirectionItem[];
  services: ServiceItem[];
  bureaux: BureauItem[];
  functions: FunctionItem[];
  grades: GradeItem[];
}

export interface PaginatedResponse<T> {
  status: string;
  pagination: {
    count: number;
    page: number;
    page_size: number;
    total_pages: number;
    next: string | null;
    previous: string | null;
  };
  results: T[];
}

// ── Directions ──────────────────────────────────────────────
export const fetchDirections = (params?: Record<string, any>) =>
  apiClient.get("/organization/directions/", { params }).then((r) => r.data);

export const fetchActiveDirections = () =>
  apiClient.get("/organization/directions/active/").then((r) => r.data);

export const createDirection = (data: Record<string, any>) =>
  apiClient.post("/organization/directions/", data).then((r) => r.data);

export const updateDirection = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/organization/directions/${id}/`, data).then((r) => r.data);

export const deleteDirection = (id: string) =>
  apiClient.delete(`/organization/directions/${id}/`).then((r) => r.data);

// ── SubDirections ──────────────────────────────────────────
export const fetchSubDirections = (params?: Record<string, any>) =>
  apiClient.get("/organization/sub-directions/", { params }).then((r) => r.data);

export const fetchActiveSubDirections = (directionId?: string) =>
  apiClient.get("/organization/sub-directions/active/", { params: directionId ? { direction: directionId } : {} }).then((r) => r.data);

export const createSubDirection = (data: Record<string, any>) =>
  apiClient.post("/organization/sub-directions/", data).then((r) => r.data);

export const updateSubDirection = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/organization/sub-directions/${id}/`, data).then((r) => r.data);

export const deleteSubDirection = (id: string) =>
  apiClient.delete(`/organization/sub-directions/${id}/`).then((r) => r.data);

// ── Services ────────────────────────────────────────────────
export const fetchServices = (params?: Record<string, any>) =>
  apiClient.get("/organization/services/", { params }).then((r) => r.data);

export const fetchActiveServices = (subDirectionId?: string) =>
  apiClient.get("/organization/services/active/", { params: subDirectionId ? { sub_direction: subDirectionId } : {} }).then((r) => r.data);

export const createService = (data: Record<string, any>) =>
  apiClient.post("/organization/services/", data).then((r) => r.data);

export const updateService = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/organization/services/${id}/`, data).then((r) => r.data);

export const deleteService = (id: string) =>
  apiClient.delete(`/organization/services/${id}/`).then((r) => r.data);

// ── Bureaux ─────────────────────────────────────────────────
export const fetchBureaux = (params?: Record<string, any>) =>
  apiClient.get("/organization/bureaux/", { params }).then((r) => r.data);

export const fetchActiveBureaux = (serviceId?: string) =>
  apiClient.get("/organization/bureaux/active/", { params: serviceId ? { service: serviceId } : {} }).then((r) => r.data);

export const createBureau = (data: Record<string, any>) =>
  apiClient.post("/organization/bureaux/", data).then((r) => r.data);

export const updateBureau = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/organization/bureaux/${id}/`, data).then((r) => r.data);

export const deleteBureau = (id: string) =>
  apiClient.delete(`/organization/bureaux/${id}/`).then((r) => r.data);

// ── Functions ──────────────────────────────────────────────
export const fetchFunctions = (params?: Record<string, any>) =>
  apiClient.get("/organization/functions/", { params }).then((r) => r.data);

export const fetchActiveFunctions = () =>
  apiClient.get("/organization/functions/active/").then((r) => r.data);

export const createFunction = (data: Record<string, any>) =>
  apiClient.post("/organization/functions/", data).then((r) => r.data);

export const updateFunction = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/organization/functions/${id}/`, data).then((r) => r.data);

export const deleteFunction = (id: string) =>
  apiClient.delete(`/organization/functions/${id}/`).then((r) => r.data);

// ── Grades ──────────────────────────────────────────────────
export const fetchGrades = (params?: Record<string, any>) =>
  apiClient.get("/organization/grades/", { params }).then((r) => r.data);

export const fetchActiveGrades = () =>
  apiClient.get("/organization/grades/active/").then((r) => r.data);

export const createGrade = (data: Record<string, any>) =>
  apiClient.post("/organization/grades/", data).then((r) => r.data);

export const updateGrade = (id: string, data: Record<string, any>) =>
  apiClient.patch(`/organization/grades/${id}/`, data).then((r) => r.data);

export const deleteGrade = (id: string) =>
  apiClient.delete(`/organization/grades/${id}/`).then((r) => r.data);

// ── Lookup (all org data in one call) ──────────────────────
export const fetchOrganizationLookup = () =>
  apiClient.get("/organization/lookup/").then((r) => r.data);
