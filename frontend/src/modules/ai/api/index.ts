import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@shared/api/apiClient";
import type { AIAnomaly, AIRecommendation, AIScore, AssistantResponse, DetectionResult, ForecastData, WhatIfData, MedicalDocumentAnalysisResult } from "../types";

// ── Query Keys ─────────────────────────────────────────────
export const AI_KEYS = {
  anomalies: {
    all: () => ["ai", "anomalies"] as const,
    unresolved: () => ["ai", "anomalies", "unresolved"] as const,
  },
  recommendations: {
    all: () => ["ai", "recommendations"] as const,
    active: () => ["ai", "recommendations", "active"] as const,
  },
  scores: {
    all: () => ["ai", "scores"] as const,
    byType: (type: string) => ["ai", "scores", type] as const,
  },
};

// ── Hooks: Anomalies ───────────────────────────────────────
export function useUnresolvedAnomalies() {
  return useQuery({
    queryKey: AI_KEYS.anomalies.unresolved(),
    queryFn: async () => {
      const { data } = await apiClient.get<{ status: string; data: AIAnomaly[] }>("/ai/anomalies/unresolved/");
      return data.data;
    },
    refetchInterval: 60_000,
  });
}

export function useResolveAnomaly() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status, note }: { id: string; status: string; note?: string }) => {
      const { data } = await apiClient.post(`/ai/anomalies/${id}/resolve/`, { status, resolution_note: note });
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: AI_KEYS.anomalies.all() });
    },
  });
}

// ── Hooks: Recommendations ─────────────────────────────────
export function useActiveRecommendations() {
  return useQuery({
    queryKey: AI_KEYS.recommendations.active(),
    queryFn: async () => {
      const { data } = await apiClient.get<{ status: string; data: AIRecommendation[] }>("/ai/recommendations/active/");
      return data.data;
    },
    refetchInterval: 120_000,
  });
}

export function useRecommendationFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, feedback, comment }: { id: string; feedback: string; comment?: string }) => {
      const { data } = await apiClient.post(`/ai/recommendations/${id}/feedback/`, { feedback, comment });
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: AI_KEYS.recommendations.all() });
    },
  });
}

// ── Hooks: AI Assistant ────────────────────────────────────
export function useAskAssistant() {
  return useMutation({
    mutationFn: async (query: string) => {
      const { data } = await apiClient.post<{ status: string; data: AssistantResponse }>("/ai/services/ask-assistant/", { query });
      return data.data;
    },
  });
}

// ── Hooks: Detection ───────────────────────────────────────
export function useDetectFraud() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ days }: { days?: number } = {}) => {
      const { data } = await apiClient.post("/ai/services/detect-fraud/", { days: days ?? 90 });
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: AI_KEYS.anomalies.all() });
    },
  });
}

export function useDetectAnomalies() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ days, method }: { days?: number; method?: string } = {}) => {
      const { data } = await apiClient.post<{ status: string; data: DetectionResult }>("/ai/services/detect-anomalies/", { days: days ?? 90, method: method ?? "ensemble" });
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: AI_KEYS.anomalies.all() });
    },
  });
}

// ── Hooks: Scores ──────────────────────────────────────────
export function useScoreBenefit() {
  return useMutation({
    mutationFn: async (benefitId: string) => {
      const { data } = await apiClient.post<{ status: string; data: AIScore }>("/ai/services/score-benefit/", { benefit_id: benefitId });
      return data.data;
    },
  });
}

// ── Hooks: Forecast ────────────────────────────────────────
export function useForecast() {
  return useMutation({
    mutationFn: async (params: { target?: string; months?: number; method?: string }) => {
      const { data } = await apiClient.post("/ai/services/forecast/", params);
      return data.data as ForecastData;
    },
  });
}

export function useWhatIf() {
  return useMutation({
    mutationFn: async (params: { budget_change_pct?: number; new_hires?: number }) => {
      const { data } = await apiClient.post("/ai/services/what-if/", params);
      return data.data as WhatIfData;
    },
  });
}

// ── Hooks: Document Analysis ───────────────────────────────
export const AI_DOC_KEYS = {
  analyses: {
    all: () => ["ai", "document-analyses"] as const,
  },
};

export function useAnalyzeDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await apiClient.post("/ai/services/analyze-document/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data.data as MedicalDocumentAnalysisResult;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: AI_DOC_KEYS.analyses.all() });
    },
  });
}

export function useDocumentAnalyses() {
  return useQuery({
    queryKey: AI_DOC_KEYS.analyses.all(),
    queryFn: async () => {
      const { data } = await apiClient.get<{ status: string; data: MedicalDocumentAnalysisResult[] }>("/ai/document-analyses/");
      return data.data;
    },
  });
}
