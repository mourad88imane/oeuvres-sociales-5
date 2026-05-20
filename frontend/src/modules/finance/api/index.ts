/**
 * FINANCE API + HOOKS
 */
import apiClient from "@shared/api/apiClient";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  FiscalYear, Budget, Payment, PaymentBatch,
  FinancialEntry, FinancialAlert, FinanceDashboard,
  PaymentFilters, BudgetFilters,
} from "../types";
import type { PaginatedResponse } from "@modules/employees/types";

const clean = (o: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(o).filter(([, v]) => v !== "" && v != null));

// ═══════════════════════════════════════════════════════════
// API FUNCTIONS
// ═══════════════════════════════════════════════════════════
export const financeApi = {
  // Fiscal years
  listFiscalYears: () =>
    apiClient.get<PaginatedResponse<FiscalYear>>("/finance/fiscal-years/"),
  getActiveFiscalYear: () =>
    apiClient.get<{ status: string; data: FiscalYear | null }>("/finance/fiscal-years/active/"),
  createFiscalYear: (data: Record<string, unknown>) =>
    apiClient.post("/finance/fiscal-years/", data),
  openFiscalYear: (id: string) =>
    apiClient.post(`/finance/fiscal-years/${id}/open/`),
  closeFiscalYear: (id: string) =>
    apiClient.post(`/finance/fiscal-years/${id}/close/`),

  // Budgets
  listBudgets: (filters: BudgetFilters = {}) =>
    apiClient.get<PaginatedResponse<Budget>>("/finance/budgets/", { params: clean(filters as Record<string, unknown>) }),
  getBudget: (id: string) =>
    apiClient.get<{ data: Budget }>(`/finance/budgets/${id}/`),
  createBudget: (data: Record<string, unknown>) =>
    apiClient.post("/finance/budgets/", data),
  updateBudget: (id: string, data: Record<string, unknown>) =>
    apiClient.patch(`/finance/budgets/${id}/`, data),
  approveBudget: (id: string) =>
    apiClient.post(`/finance/budgets/${id}/approve/`),
  getConsumptionReport: (fiscalYearId: string) =>
    apiClient.get(`/finance/budgets/consumption-report/?fiscal_year=${fiscalYearId}`),
  exportBudgets: (fiscalYearId: string) =>
    apiClient.get(`/finance/budgets/export/?fiscal_year=${fiscalYearId}`, { responseType: "blob" }),

  // Payments
  listPayments: (filters: PaymentFilters = {}) =>
    apiClient.get<PaginatedResponse<Payment>>("/finance/payments/", { params: clean(filters as Record<string, unknown>) }),
  getPayment: (id: string) =>
    apiClient.get<{ status: string; data: Payment }>(`/finance/payments/${id}/`),
  createPayment: (data: Record<string, unknown>) =>
    apiClient.post("/finance/payments/", data),
  approvePayment: (id: string) =>
    apiClient.post(`/finance/payments/${id}/approve/`),
  markPaid: (id: string, data: { bank_reference: string; executed_date?: string; paid_amount?: number }) =>
    apiClient.post(`/finance/payments/${id}/mark-paid/`, data),
  cancelPayment: (id: string, reason: string) =>
    apiClient.post(`/finance/payments/${id}/cancel/`, { reason }),
  exportPayments: (filters: PaymentFilters) =>
    apiClient.get("/finance/payments/export/", { params: clean(filters as Record<string, unknown>), responseType: "blob" }),

  // Batches
  listBatches: () =>
    apiClient.get<PaginatedResponse<PaymentBatch>>("/finance/payment-batches/"),
  createBatch: (data: Record<string, unknown>) =>
    apiClient.post("/finance/payment-batches/", data),
  approveBatch: (id: string) =>
    apiClient.post(`/finance/payment-batches/${id}/approve/`),

  // Entries
  listEntries: (params: Record<string, string> = {}) =>
    apiClient.get<PaginatedResponse<FinancialEntry>>("/finance/entries/", { params }),

  // Alerts
  listAlerts: (params: Record<string, unknown> = {}) =>
    apiClient.get<PaginatedResponse<FinancialAlert>>("/finance/alerts/", { params }),
  resolveAlert: (id: string) =>
    apiClient.post(`/finance/alerts/${id}/resolve/`),
  markAllAlertsRead: () =>
    apiClient.post("/finance/alerts/mark-all-read/"),

  // Dashboard
  getDashboard: (fiscalYearId?: string) =>
    apiClient.get<{ status: string; data: FinanceDashboard }>(
      "/finance/dashboard/",
      { params: fiscalYearId ? { fiscal_year: fiscalYearId } : {} }
    ),
};

// ═══════════════════════════════════════════════════════════
// QUERY KEYS
// ═══════════════════════════════════════════════════════════
export const FINANCE_KEYS = {
  fiscalYears:     () => ["finance","fiscal-years"] as const,
  activeFY:        () => ["finance","fiscal-years","active"] as const,
  budgets:         (f?: BudgetFilters) => ["finance","budgets", f] as const,
  budget:          (id: string) => ["finance","budgets", id] as const,
  consumptionReport:(fyId: string) => ["finance","consumption-report", fyId] as const,
  payments:        (f?: PaymentFilters) => ["finance","payments", f] as const,
  payment:         (id: string) => ["finance","payments", id] as const,
  batches:         () => ["finance","batches"] as const,
  entries:         (p?: Record<string, string>) => ["finance","entries", p] as const,
  alerts:          (p?: Record<string, unknown>) => ["finance","alerts", p] as const,
  dashboard:       (fyId?: string) => ["finance","dashboard", fyId] as const,
};

// ═══════════════════════════════════════════════════════════
// HOOKS
// ═══════════════════════════════════════════════════════════

// Fiscal years
export const useFiscalYears = () =>
  useQuery({ queryKey: FINANCE_KEYS.fiscalYears(), queryFn: () => financeApi.listFiscalYears().then(r => r.data) });

export const useActiveFiscalYear = () =>
  useQuery({ queryKey: FINANCE_KEYS.activeFY(), queryFn: () => financeApi.getActiveFiscalYear().then(r => r.data.data), staleTime: 1000*60*5 });

// Budgets
export const useBudgets = (filters: BudgetFilters = {}) =>
  useQuery({ queryKey: FINANCE_KEYS.budgets(filters), queryFn: () => financeApi.listBudgets(filters).then(r => r.data), placeholderData: p => p });

export const useConsumptionReport = (fyId: string | null) =>
  useQuery({
    queryKey: FINANCE_KEYS.consumptionReport(fyId!),
    queryFn:  () => financeApi.getConsumptionReport(fyId!).then(r => r.data),
    enabled:  !!fyId,
  });

export const useApproveBudget = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => financeApi.approveBudget(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance","budgets"] }),
  });
};

// Payments
export const usePayments = (filters: PaymentFilters = {}) =>
  useQuery({ queryKey: FINANCE_KEYS.payments(filters), queryFn: () => financeApi.listPayments(filters).then(r => r.data), placeholderData: p => p });

export const usePayment = (id: string | null) =>
  useQuery({ queryKey: FINANCE_KEYS.payment(id!), queryFn: () => financeApi.getPayment(id!).then(r => r.data.data), enabled: !!id });

export const useApprovePayment = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => financeApi.approvePayment(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["finance","payments"] });
      qc.invalidateQueries({ queryKey: FINANCE_KEYS.dashboard() });
    },
  });
};

export const useMarkPaid = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; bank_reference: string; executed_date?: string; paid_amount?: number }) =>
      financeApi.markPaid(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["finance","payments"] });
      qc.invalidateQueries({ queryKey: FINANCE_KEYS.dashboard() });
    },
  });
};

export const useCancelPayment = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => financeApi.cancelPayment(id, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance","payments"] }),
  });
};

export const useExportPayments = () =>
  useMutation({
    mutationFn: async (filters: PaymentFilters) => {
      const r = await financeApi.exportPayments(filters);
      const url = URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a"); a.href = url;
      a.download = `paiements-${new Date().toISOString().slice(0,10)}.xlsx`;
      a.click(); URL.revokeObjectURL(url);
    },
  });

// Alerts
export const useAlerts = (params: Record<string, unknown> = {}) =>
  useQuery({ queryKey: FINANCE_KEYS.alerts(params), queryFn: () => financeApi.listAlerts(params).then(r => r.data), staleTime: 0 });

export const useResolveAlert = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => financeApi.resolveAlert(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance","alerts"] }),
  });
};

// Dashboard
export const useFinanceDashboard = (fyId?: string) =>
  useQuery({
    queryKey: FINANCE_KEYS.dashboard(fyId),
    queryFn:  () => financeApi.getDashboard(fyId).then(r => r.data.data),
    staleTime: 1000 * 60 * 3,
  });

// Entries
export const useFinancialEntries = (params: Record<string, string> = {}) =>
  useQuery({
    queryKey: FINANCE_KEYS.entries(params),
    queryFn:  () => financeApi.listEntries(params).then(r => r.data),
    placeholderData: p => p,
  });
