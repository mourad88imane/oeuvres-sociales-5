import apiClient from "@shared/api/apiClient";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { DashboardStats, APIRequestLogEntry, SecurityEventEntry, AuditLogEntry, AuditStats, EndpointStatus } from "../types";

export const MONITORING_KEYS = {
  all:        () => ["monitoring"] as const,
  dashboard:  () => ["monitoring", "dashboard"] as const,
  apiLogs:    () => ["monitoring", "api-logs"] as const,
  security:   () => ["monitoring", "security"] as const,
  endpoints:  () => ["monitoring", "endpoints"] as const,
  auditLogs:  () => ["monitoring", "audit"] as const,
  auditStats: () => ["monitoring", "audit-stats"] as const,
  validations: () => ["monitoring", "validations"] as const,
};

export function useDashboardStats(hours = 24) {
  return useQuery({
    queryKey: MONITORING_KEYS.dashboard(),
    queryFn: () => apiClient.get<{ status: string; data: DashboardStats }>(
      "/monitoring/", { params: { hours } }
    ).then(r => r.data.data),
    refetchInterval: 60000,
  });
}

export function useApiLogs(params?: { is_error?: boolean; method?: string; limit?: number; days?: number }) {
  return useQuery({
    queryKey: [...MONITORING_KEYS.apiLogs(), params],
    queryFn: () => apiClient.get<{ status: string; data: APIRequestLogEntry[] }>(
      "/monitoring/api-logs/", { params }
    ).then(r => r.data.data),
    refetchInterval: 30000,
  });
}

export function useSecurityEvents(params?: { severity?: string; resolved?: string; limit?: number }) {
  return useQuery({
    queryKey: [...MONITORING_KEYS.security(), params],
    queryFn: () => apiClient.get<{ status: string; data: SecurityEventEntry[] }>(
      "/monitoring/security-events/", { params }
    ).then(r => r.data.data),
    refetchInterval: 30000,
  });
}

export function useResolveSecurityEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) =>
      apiClient.post(`/monitoring/security-events/${id}/resolve/`, { resolution_note: note }),
    onSuccess: () => qc.invalidateQueries({ queryKey: MONITORING_KEYS.security() }),
  });
}

export function useEndpointStatus() {
  return useQuery({
    queryKey: MONITORING_KEYS.endpoints(),
    queryFn: () => apiClient.get<{ status: string; data: EndpointStatus[] }>(
      "/monitoring/endpoint-status/"
    ).then(r => r.data.data),
    refetchInterval: 30000,
  });
}

export function useAuditLogs(params?: { days?: number; limit?: number; action?: string; severity?: string; user?: string }) {
  return useQuery({
    queryKey: [...MONITORING_KEYS.auditLogs(), params],
    queryFn: () => apiClient.get<{ status: string; data: AuditLogEntry[] }>(
      "/audit/logs/", { params }
    ).then(r => r.data.data),
    refetchInterval: 60000,
  });
}

export function useAuditStats(days = 30) {
  return useQuery({
    queryKey: [...MONITORING_KEYS.auditStats(), days],
    queryFn: () => apiClient.get<{ status: string; data: AuditStats }>(
      "/audit/stats/", { params: { days } }
    ).then(r => r.data.data),
  });
}
