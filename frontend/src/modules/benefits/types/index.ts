/**
 * BENEFITS TYPES — TypeScript complet
 */

// ── États workflow ─────────────────────────────────────────
export type WorkflowState =
  | "draft" | "submitted" | "under_review"
  | "on_hold" | "pending_director_approval"
  | "validated" | "paid" | "rejected" | "cancelled";

export type Priority   = "low" | "normal" | "high" | "urgent";
export type BenefitCategory = "medical" | "loan" | "purchase" | "bonus" | "aid" | "other";
export type CommentType = "internal" | "requester" | "system";
export type DocType = "prescription" | "invoice" | "certificate" | "identity" | "salary_slip" | "bank_details" | "other";

// ── Config état (couleurs, labels) ────────────────────────
export interface StateConfig {
  label: string;
  color: string;
  bg: string;
  text: string;
  is_initial: boolean;
  is_final: boolean;
  description: string;
}

// ── Type de prestation ────────────────────────────────────
export interface BenefitType {
  id: string;
  code: string;
  name: string;
  category: BenefitCategory;
  category_display: string;
  description: string;
  is_active: boolean;
  max_amount: number | null;
  min_seniority_years: number | null;
  max_per_year: number | null;
  requires_attachments: boolean;
  required_attachments_description: string;
  target_processing_days: number | null;
}

// ── Pièce jointe ──────────────────────────────────────────
export interface Attachment {
  id: string;
  original_name: string;
  doc_type: DocType;
  doc_type_display: string;
  description: string;
  file_size: number;
  file_size_display: string;
  mime_type: string;
  uploaded_by_name: string | null;
  file_url: string | null;
  created_at: string;
}

// ── Commentaire ───────────────────────────────────────────
export interface Comment {
  id: string;
  author_name: string;
  author_role: string;
  comment_type: CommentType;
  type_display: string;
  content: string;
  workflow_state_at_time: string;
  created_at: string;
}

// ── Log workflow ──────────────────────────────────────────
export interface WorkflowLog {
  id: string;
  from_state: WorkflowState;
  from_state_label: string;
  to_state: WorkflowState;
  to_state_label: string;
  transition_name: string;
  actor_email: string;
  actor_role: string;
  reason: string;
  duration_seconds: number | null;
  duration_label: string;
  is_reversal: boolean;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  timestamp: string;
}

// ── Transition disponible ─────────────────────────────────
export interface AvailableTransition {
  to_state: WorkflowState;
  label: string;
  state_label: string;
  can_execute: boolean;
  blocked_reason: string;
  requires_reason: boolean;
  severity: string;
}

// ── Benefit liste ─────────────────────────────────────────
export interface BenefitListItem {
  id: string;
  reference: string;
  title: string;
  workflow_state: WorkflowState;
  state_label: string;
  state_config: StateConfig;
  employee: string;
  employee_name: string;
  employee_matricule: string;
  department_name: string;
  benefit_type: string;
  benefit_type_name: string;
  benefit_type_code: string;
  benefit_category: BenefitCategory;
  requested_amount: number;
  approved_amount: number | null;
  paid_amount: number | null;
  amount_display: string;
  priority: Priority;
  priority_display: string;
  is_overdue: boolean;
  processing_days: number | null;
  submitted_at: string | null;
  validated_at: string | null;
  paid_at: string | null;
  due_date: string | null;
  attachments_count: number;
  ai_anomaly_flag: boolean;
  risk_score: number | null;
  created_at: string;
  updated_at: string;
}

// ── Benefit détail ────────────────────────────────────────
export interface Benefit extends BenefitListItem {
  description: string;
  benefit_type_info: BenefitType;
  beneficiary: string | null;
  payment_reference: string;
  payment_method: string;
  payment_method_display: string;
  rejection_reason: string;
  internal_notes: string;
  validated_by_name: string | null;
  paid_by_name: string | null;
  rejected_at: string | null;
  ai_score: number | null;
  ai_metadata: Record<string, unknown>;
  attachments: Attachment[];
  comments: Comment[];
  available_transitions: AvailableTransition[];
  last_transition_at: string | null;
  last_transition_reason: string;
  created_by_name: string | null;
}

// ── Formulaires ───────────────────────────────────────────
export interface BenefitCreatePayload {
  employee: string;
  benefit_type: string;
  beneficiary?: string;
  title: string;
  description?: string;
  requested_amount: number;
  priority?: Priority;
  due_date?: string;
  internal_notes?: string;
}

export interface TransitionPayload {
  to_state: WorkflowState;
  reason?: string;
  approved_amount?: number;
  payment_reference?: string;
  paid_amount?: number;
  comment?: string;
}

// ── Statistiques ─────────────────────────────────────────
export interface BenefitStatistics {
  total: number;
  by_state: Record<string, number>;
  pending_count: number;
  paid_count: number;
  rejected_count: number;
  anomaly_count: number;
  total_requested: number;
  total_approved: number;
  total_paid: number;
  avg_processing_days: number | null;
  sla_rate: number | null;
  by_type: { benefit_type__code: string; benefit_type__name: string; count: number; total_amount: number }[];
  by_priority: { priority: string; count: number }[];
  monthly_trend: { month: string; count: number; amount: number }[];
}

// ── Filtres ───────────────────────────────────────────────
export interface BenefitFilters {
  search?: string;
  state?: WorkflowState | "";
  benefit_type?: string;
  employee?: string;
  department?: string;
  priority?: Priority | "";
  ai_anomaly?: boolean | "";
  date_from?: string;
  date_to?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

// ── Config UI ─────────────────────────────────────────────
export const STATE_UI: Record<WorkflowState, { label: string; badgeClass: string; dotClass: string }> = {
  draft:        { label: "Brouillon",              badgeClass: "bg-gray-100 text-gray-700",      dotClass: "bg-gray-400"   },
  submitted:    { label: "Soumise",                badgeClass: "bg-blue-100 text-blue-700",      dotClass: "bg-blue-500"   },
  under_review: { label: "En instruction",         badgeClass: "bg-purple-100 text-purple-700",  dotClass: "bg-purple-500" },
  on_hold:      { label: "En attente",             badgeClass: "bg-amber-100 text-amber-700",    dotClass: "bg-amber-500"  },
  pending_director_approval: { label: "En attente du directeur", badgeClass: "bg-pink-100 text-pink-700", dotClass: "bg-pink-500" },
  validated:    { label: "Validée",                badgeClass: "bg-emerald-100 text-emerald-700",dotClass: "bg-emerald-500"},
  paid:         { label: "Payée",                  badgeClass: "bg-green-100 text-green-700",    dotClass: "bg-green-500"  },
  rejected:     { label: "Rejetée",                badgeClass: "bg-red-100 text-red-700",        dotClass: "bg-red-500"    },
  cancelled:    { label: "Annulée",                badgeClass: "bg-gray-100 text-gray-500",      dotClass: "bg-gray-300"   },
};

export const PRIORITY_UI: Record<Priority, { label: string; badgeClass: string }> = {
  low:    { label: "Basse",   badgeClass: "bg-gray-100 text-gray-600"   },
  normal: { label: "Normale", badgeClass: "bg-blue-50 text-blue-600"    },
  high:   { label: "Haute",   badgeClass: "bg-orange-100 text-orange-700"},
  urgent: { label: "Urgente", badgeClass: "bg-red-100 text-red-700"      },
};

export const CATEGORY_UI: Record<BenefitCategory, { label: string; icon: string }> = {
  medical:  { label: "Médical",         icon: "🏥" },
  loan:     { label: "Prêt",            icon: "💰" },
  purchase: { label: "Achat facilité",  icon: "🛒" },
  bonus:    { label: "Prime",           icon: "⭐" },
  aid:      { label: "Aide exception.", icon: "🤝" },
  other:    { label: "Autre",           icon: "📋" },
};

// Ordre de la timeline workflow
export const WORKFLOW_ORDER: WorkflowState[] = [
  "draft", "submitted", "under_review", "pending_director_approval", "validated", "paid"
];
