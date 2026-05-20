/**
 * BENEFITS HOOKS — TanStack Query
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { benefitApi } from "../api";
import type {
  BenefitFilters, BenefitCreatePayload, TransitionPayload,
} from "../types";

export const BENEFIT_KEYS = {
  all:        ["benefits"] as const,
  lists:      () => [...BENEFIT_KEYS.all, "list"] as const,
  list:       (f: BenefitFilters) => [...BENEFIT_KEYS.lists(), f] as const,
  detail:     (id: string) => [...BENEFIT_KEYS.all, "detail", id] as const,
  log:        (id: string) => [...BENEFIT_KEYS.all, "log",    id] as const,
  transitions:(id: string) => [...BENEFIT_KEYS.all, "transitions", id] as const,
  statistics: (p?: Record<string, string>) => [...BENEFIT_KEYS.all, "stats", p] as const,
  types:      () => ["benefit-types"] as const,
};

// ── Lectures ──────────────────────────────────────────────
export function useBenefits(filters: BenefitFilters = {}) {
  return useQuery({
    queryKey: BENEFIT_KEYS.list(filters),
    queryFn:  () => benefitApi.list(filters).then(r => r.data),
    placeholderData: prev => prev,
  });
}

export function useBenefit(id: string | null) {
  return useQuery({
    queryKey: BENEFIT_KEYS.detail(id!),
    queryFn:  () => benefitApi.get(id!).then(r => r.data.data),
    enabled:  !!id,
    staleTime: 0,
  });
}

export function useBenefitWorkflowLog(id: string | null) {
  return useQuery({
    queryKey: BENEFIT_KEYS.log(id!),
    queryFn:  () => benefitApi.getWorkflowLog(id!).then(r => r.data),
    enabled:  !!id,
    staleTime: 0,
  });
}

export function useAvailableTransitions(id: string | null) {
  return useQuery({
    queryKey: BENEFIT_KEYS.transitions(id!),
    queryFn:  () => benefitApi.getAvailableTransitions(id!).then(r => r.data.data),
    enabled:  !!id,
    staleTime: 0,
  });
}

export function useBenefitStatistics(params?: Record<string, string>) {
  return useQuery({
    queryKey: BENEFIT_KEYS.statistics(params),
    queryFn:  () => benefitApi.getStatistics(params).then(r => r.data.data),
    staleTime: 1000 * 60 * 3,
  });
}

export function useBenefitTypes(params?: { active_only?: boolean; category?: string }) {
  return useQuery({
    queryKey: [...BENEFIT_KEYS.types(), params],
    queryFn:  () => benefitApi.listTypes(params).then(r => r.data),
    staleTime: 1000 * 60 * 10,
  });
}

// ── Mutations ─────────────────────────────────────────────
export function useCreateBenefit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BenefitCreatePayload) =>
      benefitApi.create(data).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.lists() });
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.statistics() });
    },
  });
}

export function useTransition(benefitId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: TransitionPayload) =>
      benefitApi.transition(benefitId, payload).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.detail(benefitId) });
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.log(benefitId) });
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.transitions(benefitId) });
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.lists() });
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.statistics() });
    },
  });
}

export function useUploadAttachment(benefitId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, docType, description }: { file: File; docType: string; description?: string }) =>
      benefitApi.uploadAttachment(benefitId, file, docType, description),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.detail(benefitId) });
    },
  });
}

export function useAddComment(benefitId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ content, commentType }: { content: string; commentType?: string }) =>
      benefitApi.addComment(benefitId, content, commentType),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.detail(benefitId) });
    },
  });
}

export function useDeleteBenefit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => benefitApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.lists() });
      qc.invalidateQueries({ queryKey: BENEFIT_KEYS.statistics() });
    },
  });
}
