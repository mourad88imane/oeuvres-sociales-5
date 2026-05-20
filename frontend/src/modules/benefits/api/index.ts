/**
 * BENEFITS API
 */
import apiClient from "@shared/api/apiClient";
import type {
  BenefitFilters, BenefitCreatePayload, TransitionPayload,
  Benefit, BenefitListItem, BenefitType, BenefitStatistics,
  WorkflowLog, AvailableTransition,
} from "../types";
import type { PaginatedResponse } from "@modules/employees/types";

const clean = (f: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(f).filter(([, v]) => v !== "" && v != null));

export const benefitApi = {
  // ── Liste et détail ───────────────────────────────────
  list: (filters: BenefitFilters = {}) =>
    apiClient.get<PaginatedResponse<BenefitListItem>>("/benefits/", { params: clean(filters as Record<string, unknown>) }),

  get: (id: string) =>
    apiClient.get<{ status: string; data: Benefit }>(`/benefits/${id}/`),

  // ── CRUD ──────────────────────────────────────────────
  create: (data: BenefitCreatePayload) =>
    apiClient.post<{ status: string; data: Benefit }>("/benefits/", data),

  update: (id: string, data: Partial<BenefitCreatePayload>) =>
    apiClient.patch<{ status: string; data: Benefit }>(`/benefits/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/benefits/${id}/`),

  // ── Workflow ──────────────────────────────────────────
  transition: (id: string, payload: TransitionPayload) =>
    apiClient.post<{
      status: string; message: string;
      from_state: string; to_state: string;
      data: Benefit;
    }>(`/benefits/${id}/transition/`, payload),

  getAvailableTransitions: (id: string) =>
    apiClient.get<{ status: string; data: AvailableTransition[] }>(
      `/benefits/${id}/available-transitions/`
    ),

  getWorkflowLog: (id: string) =>
    apiClient.get<{ status: string; count: number; data: WorkflowLog[] }>(
      `/benefits/${id}/workflow-log/`
    ),

  // ── Pièces jointes ────────────────────────────────────
  uploadAttachment: (id: string, file: File, docType: string, description?: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", docType);
    if (description) form.append("description", description);
    return apiClient.post(`/benefits/${id}/attachments/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  deleteAttachment: (id: string, attId: string) =>
    apiClient.delete(`/benefits/${id}/attachments/${attId}/`),

  // ── Commentaires ──────────────────────────────────────
  addComment: (id: string, content: string, commentType: string = "internal") =>
    apiClient.post(`/benefits/${id}/comments/`, { content, comment_type: commentType }),

  // ── Types ─────────────────────────────────────────────
  listTypes: (params?: { active_only?: boolean; category?: string }) =>
    apiClient.get<PaginatedResponse<BenefitType>>("/benefits/types/", { params }),

  // ── Statistiques ─────────────────────────────────────
  getStatistics: (params?: Record<string, string>) =>
    apiClient.get<{ status: string; data: BenefitStatistics }>(
      "/benefits/statistics/", { params }
    ),
};
