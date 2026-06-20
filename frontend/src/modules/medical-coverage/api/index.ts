import apiClient from "@shared/api/apiClient";
import { useQuery } from "@tanstack/react-query";
import type {
  MedicalCoverageVoucher, MedicalCoverageCreatePayload,
  MedicalCoverageType, MedicalProvider,
  MedicalCoverageFilters, CoverageStatistics,
  EmployeeInfoResponse, AvailableTransition, WorkflowLogEntry,
} from "../types";
import type { PaginatedResponse } from "@modules/employees/types";

const clean = (f: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(f).filter(([, v]) => v !== "" && v != null));

export const medicalCoverageApi = {
  list: (filters: MedicalCoverageFilters = {}) =>
    apiClient.get<PaginatedResponse<MedicalCoverageVoucher>>("/medical-coverage/vouchers/", {
      params: clean(filters as Record<string, unknown>),
    }),

  get: (id: string) =>
    apiClient.get<{ status: string; data: MedicalCoverageVoucher }>(`/medical-coverage/vouchers/${id}/`),

  create: (data: MedicalCoverageCreatePayload) =>
    apiClient.post<{ status: string; data: MedicalCoverageVoucher }>("/medical-coverage/vouchers/", data),

  update: (id: string, data: Partial<MedicalCoverageCreatePayload>) =>
    apiClient.patch<{ status: string; data: MedicalCoverageVoucher }>(`/medical-coverage/vouchers/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/medical-coverage/vouchers/${id}/`),

  transition: (id: string, to_state: string, reason?: string) =>
    apiClient.post<{ status: string; data: MedicalCoverageVoucher }>(
      `/medical-coverage/vouchers/${id}/transition/`, { to_state, reason },
    ),

  getAvailableTransitions: (id: string) =>
    apiClient.get<{ status: string; data: AvailableTransition[] }>(
      `/medical-coverage/vouchers/${id}/available_transitions/`,
    ),

  getWorkflowLog: (id: string) =>
    apiClient.get<{ status: string; count: number; data: WorkflowLogEntry[] }>(
      `/medical-coverage/vouchers/${id}/workflow_log/`,
    ),

  getStatistics: (coverage_type?: string) =>
    apiClient.get<{ status: string; data: CoverageStatistics }>("/medical-coverage/vouchers/statistics/", {
      params: coverage_type ? { coverage_type } : {},
    }),

  getEmployeeInfo: (employee_id: string, coverage_type?: string) =>
    apiClient.get<{ status: string; data: EmployeeInfoResponse }>("/medical-coverage/vouchers/employee_info/", {
      params: { employee_id, coverage_type: coverage_type || "" },
    }),

  listTypes: () =>
    apiClient.get<MedicalCoverageType[]>("/medical-coverage/types/"),

  listProviders: (params?: { coverage_type?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<MedicalProvider>>("/medical-coverage/providers/", {
      params: clean(params || {}),
    }),
};

export const MEDICAL_COVERAGE_KEYS = {
  statistics: (type?: string) => ["medical-coverage", "statistics", type] as const,
  types: () => ["medical-coverage", "types"] as const,
  list: (filters?: MedicalCoverageFilters) => ["medical-coverage", "list", filters] as const,
};

export const useMedicalCoverageStatistics = (coverage_type?: string) =>
  useQuery({
    queryKey: MEDICAL_COVERAGE_KEYS.statistics(coverage_type),
    queryFn: () => medicalCoverageApi.getStatistics(coverage_type).then(r => r.data.data),
    staleTime: 1000 * 60 * 2,
  });

export const useMedicalCoverageTypes = () =>
  useQuery({
    queryKey: MEDICAL_COVERAGE_KEYS.types(),
    queryFn: () => medicalCoverageApi.listTypes().then(r => r.data),
    staleTime: 1000 * 60 * 5,
  });
