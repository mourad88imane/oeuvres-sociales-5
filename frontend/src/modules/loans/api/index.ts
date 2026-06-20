import apiClient from "@shared/api/apiClient";
import type {
  Loan, LoanListItem, LoanCreatePayload, LoanUpdatePayload,
  LoanFilters, TransitionPayload, PaginatedResponse,
} from "../types";

const cleanParams = (filters: LoanFilters) =>
  Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== "" && v != null));

export const loanApi = {
  list: (filters: LoanFilters = {}) =>
    apiClient.get<PaginatedResponse<LoanListItem>>("/loans/", { params: cleanParams(filters) }),

  get: (id: string) =>
    apiClient.get<{ status: string; data: Loan }>(`/loans/${id}/`),

  create: (data: LoanCreatePayload) =>
    apiClient.post<{ status: string; data: Loan }>("/loans/", data),

  update: (id: string, data: LoanUpdatePayload) =>
    apiClient.patch<{ status: string; data: Loan }>(`/loans/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/loans/${id}/`),

  transition: (id: string, payload: TransitionPayload) =>
    apiClient.post<{ status: string; data: Loan }>(`/loans/${id}/transition/`, payload),

  getAvailableTransitions: (id: string) =>
    apiClient.get<{ status: string; data: any[] }>(`/loans/${id}/available-transitions/`),

  getWorkflowLog: (id: string) =>
    apiClient.get<{ status: string; count: number; data: any[] }>(`/loans/${id}/workflow-log/`),

  uploadAttachment: (id: string, file: File, docType: string, description: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", docType);
    form.append("description", description);
    return apiClient.post(`/loans/${id}/attachments/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  deleteAttachment: (loanId: string, attId: string) =>
    apiClient.delete(`/loans/${loanId}/attachments/${attId}/`),

  addComment: (id: string, content: string, commentType = "internal") =>
    apiClient.post(`/loans/${id}/comments/`, { content, comment_type: commentType }),

  getStatistics: (params?: Record<string, string>) =>
    apiClient.get<{ status: string; data: any }>("/loans/statistics/", { params }),
};
