export type WorkflowState =
  | "draft" | "submitted" | "under_review" | "on_hold"
  | "pending_director_approval"
  | "validated" | "paid" | "rejected" | "cancelled";

export interface LoanListItem {
  id: string;
  reference: string;
  reason: string;
  workflow_state: WorkflowState;
  state_label: string;
  state_config: Record<string, unknown>;
  employee: string;
  employee_name: string;
  employee_matricule: string;
  department_name: string;
  requested_amount: number;
  approved_amount: number | null;
  amount_display: string;
  submitted_at: string | null;
  validated_at: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AvailableTransition {
  to_state: string;
  label: string;
  state_label: string;
  can_execute: boolean;
  blocked_reason: string;
  requires_reason: boolean;
  severity: string;
}

export interface LoanAttachment {
  id: string;
  original_name: string;
  doc_type: string;
  doc_type_display: string;
  description: string;
  file_size: number;
  file_size_display: string;
  mime_type: string;
  uploaded_by_name: string | null;
  file_url: string | null;
  created_at: string;
}

export interface LoanComment {
  id: string;
  author_name: string;
  author_role: string;
  comment_type: string;
  type_display: string;
  content: string;
  workflow_state_at_time: string;
  created_at: string;
}

export interface Loan extends LoanListItem {
  description: string;
  paid_amount: number | null;
  monthly_instalment: number | null;
  instalment_count: number | null;
  instalment_display: string;
  rejected_at: string | null;
  validated_by_name: string | null;
  paid_by_name: string | null;
  rejection_reason: string;
  payment_reference: string;
  attachments: LoanAttachment[];
  comments: LoanComment[];
  available_transitions: AvailableTransition[];
  last_transition_at: string | null;
  last_transition_reason: string;
  created_by_name: string;
}

export interface LoanCreatePayload {
  employee: string;
  requested_amount: number;
  reason: string;
  description?: string;
}

export interface LoanUpdatePayload {
  reason?: string;
  description?: string;
  requested_amount?: number;
}

export interface LoanFilters {
  page?: number;
  page_size?: number;
  search?: string;
  state?: string;
  employee?: string;
  department?: string;
  date_from?: string;
  date_to?: string;
  ordering?: string;
}

export interface TransitionPayload {
  to_state: string;
  reason?: string;
  approved_amount?: number;
  monthly_instalment?: number;
  instalment_count?: number;
  payment_reference?: string;
  paid_amount?: number;
  comment?: string;
}

export interface Pagination {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  next: string | null;
  previous: string | null;
}

export interface PaginatedResponse<T> {
  status: string;
  pagination: Pagination;
  results: T[];
}

export interface WorkflowLogEntry {
  id: string;
  from_state: string;
  from_state_label: string;
  to_state: string;
  to_state_label: string;
  transition_name: string;
  actor_email: string;
  actor_role: string;
  reason: string;
  duration_seconds: number | null;
  duration_label: string;
  is_reversal: boolean;
  severity: string;
  timestamp: string;
}

export interface LoanStatistics {
  total: number;
  by_state: Record<string, number>;
  pending_count: number;
  paid_count: number;
  rejected_count: number;
  total_requested: number;
  total_approved: number;
  total_paid: number;
}

export const STATE_UI: Record<WorkflowState, { label: string; badgeClass: string; dotClass: string }> = {
  draft:        { label: "Brouillon",              badgeClass: "bg-gray-100 text-gray-700",     dotClass: "bg-gray-400" },
  submitted:    { label: "Soumise",                badgeClass: "bg-blue-100 text-blue-700",     dotClass: "bg-blue-500" },
  under_review: { label: "En instruction",         badgeClass: "bg-purple-100 text-purple-700", dotClass: "bg-purple-500" },
  on_hold:      { label: "En attente",             badgeClass: "bg-amber-100 text-amber-700",   dotClass: "bg-amber-500" },
  pending_director_approval: { label: "En attente du directeur", badgeClass: "bg-pink-100 text-pink-700", dotClass: "bg-pink-500" },
  validated:    { label: "Validée",                badgeClass: "bg-emerald-100 text-emerald-700", dotClass: "bg-emerald-500" },
  paid:         { label: "Payée",                  badgeClass: "bg-green-100 text-green-700",    dotClass: "bg-green-500" },
  rejected:     { label: "Rejetée",                badgeClass: "bg-red-100 text-red-700",       dotClass: "bg-red-500" },
  cancelled:    { label: "Annulée",                badgeClass: "bg-gray-100 text-gray-500",     dotClass: "bg-gray-400" },
};

export const WORKFLOW_ORDER: WorkflowState[] = [
  "draft", "submitted", "under_review", "pending_director_approval", "validated", "paid",
];
