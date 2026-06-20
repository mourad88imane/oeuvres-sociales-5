export type RequestCategory = "analysis" | "imaging" | "center";
export type RequestStatus = "draft" | "submitted" | "pending_approval" | "pending_manager_approval" | "pending_director_approval" | "validated" | "rejected" | "printed" | "closed";

export interface MedicalCoverageRequest {
  id: string;
  request_number: string;
  category: RequestCategory;
  category_display: string;
  partner: string;
  partner_name: string;
  employee: string;
  employee_name: string;
  employee_matricule: string;
  beneficiary: string | null;
  beneficiary_name: string | null;
  coverage_date: string;
  validation_date: string | null;
  observation: string;
  workflow_state: RequestStatus;
  state_label: string;
  created_at: string;
  created_by_name: string;
  available_transitions?: AvailableTransition[];
}

export interface AvailableTransition {
  to_state: RequestStatus;
  state_label: string;
  label: string;
  can_execute: boolean;
  blocked_reason: string;
  requires_reason: boolean;
  severity: string;
}

export interface MedicalCoverageRequestCreatePayload {
  category: RequestCategory;
  partner: string;
  employee: string;
  beneficiary?: string;
  coverage_date: string;
  observation?: string;
}

export interface RequestStatistics {
  total: number;
  pending: number;
  validated: number;
  printed: number;
  by_partner: { partner__name: string; partner__id: string; count: number }[];
  by_month: { month: number; count: number }[];
}

export const REQUEST_STATUS_UI: Record<RequestStatus, { label: string; color: string; bg: string }> = {
  draft:              { label: "Brouillon",                  color: "#6b6963", bg: "rgba(138,136,130,0.1)" },
  submitted:          { label: "Soumise",                    color: "#3b82f6", bg: "rgba(59,130,246,0.1)" },
  pending_approval:   { label: "En attente d'approbation",  color: "#f59e0b", bg: "rgba(245,158,11,0.1)" },
  pending_manager_approval: { label: "En attente du chef de service", color: "#f97316", bg: "rgba(249,115,22,0.1)" },
  pending_director_approval: { label: "En attente du directeur", color: "#ec4899", bg: "rgba(236,72,153,0.1)" },
  validated:          { label: "Validée",                    color: "#16a34a", bg: "rgba(34,197,94,0.1)" },
  rejected:           { label: "Rejetée",                    color: "#dc2626", bg: "rgba(239,68,68,0.1)" },
  printed:            { label: "Imprimée",                   color: "#9333ea", bg: "rgba(147,51,234,0.1)" },
  closed:             { label: "Clôturée",                   color: "#8a8882", bg: "rgba(138,136,130,0.08)" },
};

export const REQUEST_WORKFLOW_ORDER: RequestStatus[] = [
  "draft", "submitted", "pending_approval", "pending_manager_approval", "pending_director_approval", "validated", "printed", "closed",
];
