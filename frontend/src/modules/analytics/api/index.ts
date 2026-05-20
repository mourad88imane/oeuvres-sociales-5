import apiClient from "@shared/api/apiClient";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PaginatedResponse } from "@modules/employees/types";
import type {
  GlobalDashboardData, KpiValue, KpiHistory,
  ReportDefinition, DataExport, DashboardWidget, AnalyticsFilter,
} from "../types";

const clean = (o: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(o).filter(([, v]) => v !== "" && v != null));

export const analyticsApi = {
  getGlobalDashboard: (params: AnalyticsFilter = {}) =>
    apiClient.get<{ status: string; data: GlobalDashboardData }>("/dashboard/", { params: clean(params as Record<string, unknown>) }),

  getSummary: () =>
    apiClient.get<{ status: string; data: GlobalDashboardData["summary"] }>("/reporting/analytics/summary/"),

  getTrends: (months = 12) =>
    apiClient.get<{ status: string; data: GlobalDashboardData["trends"] }>(`/reporting/analytics/trends/?months=${months}`),

  getTopStats: (limit = 10) =>
    apiClient.get<{ status: string; data: GlobalDashboardData["top"] }>(`/reporting/analytics/top/?limit=${limit}`),

  getGlobalData: (params: AnalyticsFilter = {}) =>
    apiClient.get<{ status: string; data: GlobalDashboardData }>("/reporting/analytics/global_data/", { params: clean(params as Record<string, unknown>) }),

  getKpis: () =>
    apiClient.get<{ status: string; data: KpiValue[] }>("/reporting/kpis/values/"),

  getKpiHistory: (code: string, days = 90) =>
    apiClient.get<{ status: string; data: KpiHistory[] }>(`/reporting/kpis/history/?code=${code}&days=${days}`),

  snapshotKpis: () =>
    apiClient.post("/reporting/kpis/snapshot/"),

  listReports: (category = "") =>
    apiClient.get<PaginatedResponse<ReportDefinition>>(`/reporting/reports/${category ? `?category=${category}` : ""}`),

  generateReport: (id: string, data: { format?: string; filters?: Record<string, unknown>; date_from?: string; date_to?: string }) =>
    apiClient.post<{ status: string; data: DataExport }>(`/reporting/reports/${id}/generate/`, data),

  listExports: (params: Record<string, unknown> = {}) =>
    apiClient.get<PaginatedResponse<DataExport>>("/reporting/exports/", { params: clean(params) }),

  listWidgets: () =>
    apiClient.get<{ status: string; data: DashboardWidget[] }>("/reporting/widgets/my_widgets/"),
};

export const ANALYTICS_KEYS = {
  dashboard: (p?: AnalyticsFilter) => ["analytics", "dashboard", p] as const,
  summary:   () => ["analytics", "summary"] as const,
  trends:    (m?: number) => ["analytics", "trends", m] as const,
  top:       (l?: number) => ["analytics", "top", l] as const,
  globalData:(p?: AnalyticsFilter) => ["analytics", "global", p] as const,
  kpis:      () => ["analytics", "kpis"] as const,
  kpiHistory:(c: string, d?: number) => ["analytics", "kpi-history", c, d] as const,
  reports:   (c?: string) => ["analytics", "reports", c] as const,
  exports:   (p?: Record<string, unknown>) => ["analytics", "exports", p] as const,
  widgets:   () => ["analytics", "widgets"] as const,
};

export const useGlobalDashboard = (params: AnalyticsFilter = {}) =>
  useQuery({
    queryKey: ANALYTICS_KEYS.dashboard(params),
    queryFn: () => analyticsApi.getGlobalDashboard(params).then(r => r.data.data),
    staleTime: 1000 * 60 * 2,
  });

export const useAnalyticsSummary = () =>
  useQuery({
    queryKey: ANALYTICS_KEYS.summary(),
    queryFn: () => analyticsApi.getSummary().then(r => r.data.data),
    staleTime: 1000 * 60 * 3,
  });

export const useAnalyticsTrends = (months = 12) =>
  useQuery({
    queryKey: ANALYTICS_KEYS.trends(months),
    queryFn: () => analyticsApi.getTrends(months).then(r => r.data.data),
    staleTime: 1000 * 60 * 5,
  });

export const useAnalyticsTop = (limit = 10) =>
  useQuery({
    queryKey: ANALYTICS_KEYS.top(limit),
    queryFn: () => analyticsApi.getTopStats(limit).then(r => r.data.data),
    staleTime: 1000 * 60 * 5,
  });

export const useGlobalAnalytics = (params: AnalyticsFilter = {}) =>
  useQuery({
    queryKey: ANALYTICS_KEYS.globalData(params),
    queryFn: () => analyticsApi.getGlobalData(params).then(r => r.data.data),
    staleTime: 1000 * 60 * 2,
  });

export const useKpis = () =>
  useQuery({
    queryKey: ANALYTICS_KEYS.kpis(),
    queryFn: () => analyticsApi.getKpis().then(r => r.data.data),
    staleTime: 1000 * 60 * 3,
  });

export const useKpiHistory = (code: string, days = 90) =>
  useQuery({
    queryKey: ANALYTICS_KEYS.kpiHistory(code, days),
    queryFn: () => analyticsApi.getKpiHistory(code, days).then(r => r.data.data),
    enabled: !!code,
    staleTime: 1000 * 60 * 5,
  });

export const useSnapshotKpis = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => analyticsApi.snapshotKpis(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["analytics", "kpis"] }),
  });
};

export const useReports = (category = "") =>
  useQuery({
    queryKey: ANALYTICS_KEYS.reports(category),
    queryFn: () => analyticsApi.listReports(category).then(r => r.data),
    placeholderData: p => p,
    staleTime: 1000 * 60 * 5,
  });

export const useGenerateReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; format?: string; filters?: Record<string, unknown> }) =>
      analyticsApi.generateReport(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["analytics", "exports"] }),
  });
};

export const useExports = (params: Record<string, unknown> = {}, poll = false) =>
  useQuery({
    queryKey: ANALYTICS_KEYS.exports(params),
    queryFn: () => analyticsApi.listExports(params).then(r => r.data),
    placeholderData: p => p,
    refetchInterval: poll ? 5000 : false,
  });
