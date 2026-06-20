import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { loanApi } from "../api";
import type { LoanFilters, LoanCreatePayload, LoanUpdatePayload, TransitionPayload } from "../types";

export const LOAN_KEYS = {
  all:         ["loans"] as const,
  lists:       () => [...LOAN_KEYS.all, "list"] as const,
  list:        (f: LoanFilters) => [...LOAN_KEYS.lists(), f] as const,
  detail:      (id: string) => [...LOAN_KEYS.all, "detail", id] as const,
  log:         (id: string) => [...LOAN_KEYS.all, "log", id] as const,
  transitions: (id: string) => [...LOAN_KEYS.all, "transitions", id] as const,
  statistics:  (p?: Record<string, string>) => [...LOAN_KEYS.all, "stats", p] as const,
};

export function useLoans(filters: LoanFilters = {}) {
  return useQuery({
    queryKey: LOAN_KEYS.list(filters),
    queryFn:  () => loanApi.list(filters).then((r) => r.data),
    placeholderData: (prev) => prev,
  });
}

export function useLoan(id: string | null) {
  return useQuery({
    queryKey: LOAN_KEYS.detail(id!),
    queryFn:  () => loanApi.get(id!).then((r) => r.data.data),
    enabled:  !!id,
  });
}

export function useWorkflowLog(id: string | null) {
  return useQuery({
    queryKey: LOAN_KEYS.log(id!),
    queryFn:  () => loanApi.getWorkflowLog(id!).then((r) => r.data),
    enabled:  !!id,
  });
}

export function useLoanStatistics(params?: Record<string, string>) {
  return useQuery({
    queryKey: LOAN_KEYS.statistics(params),
    queryFn:  () => loanApi.getStatistics(params).then((r) => r.data.data),
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateLoan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LoanCreatePayload) =>
      loanApi.create(data).then((r) => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LOAN_KEYS.lists() });
      qc.invalidateQueries({ queryKey: LOAN_KEYS.statistics() });
    },
  });
}

export function useUpdateLoan(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: LoanUpdatePayload) =>
      loanApi.update(id, data).then((r) => r.data.data),
    onSuccess: (updated) => {
      qc.setQueryData(LOAN_KEYS.detail(id), updated);
      qc.invalidateQueries({ queryKey: LOAN_KEYS.lists() });
    },
  });
}

export function useDeleteLoan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => loanApi.delete(id),
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: LOAN_KEYS.detail(id) });
      qc.invalidateQueries({ queryKey: LOAN_KEYS.lists() });
      qc.invalidateQueries({ queryKey: LOAN_KEYS.statistics() });
    },
  });
}

export function useAvailableTransitions(id: string | null) {
  return useQuery({
    queryKey: LOAN_KEYS.transitions(id!),
    queryFn:  () => loanApi.getAvailableTransitions(id!).then((r) => r.data.data),
    enabled:  !!id,
    staleTime: 0,
  });
}

export function useTransition(loanId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: TransitionPayload) =>
      loanApi.transition(loanId, payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LOAN_KEYS.detail(loanId) });
      qc.invalidateQueries({ queryKey: LOAN_KEYS.lists() });
      qc.invalidateQueries({ queryKey: LOAN_KEYS.statistics() });
    },
  });
}
