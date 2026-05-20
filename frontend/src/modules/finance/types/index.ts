/**
 * FINANCE TYPES — TypeScript complet
 */

export type FiscalYearStatus = "draft" | "open" | "closed" | "archived";
export type BudgetStatus     = "draft" | "approved" | "active" | "closed";
export type PaymentStatus    = "pending" | "approved" | "processing" | "paid" | "failed" | "cancelled" | "reversed";
export type BatchStatus      = "draft" | "submitted" | "approved" | "sent" | "confirmed" | "rejected";
export type AlertSeverity    = "info" | "warning" | "critical";
export type PaymentMethod    = "virement" | "cheque" | "caisse" | "ccp";
export type EntryType        = "debit" | "credit" | "adjustment" | "reversal" | "opening" | "closing";
export type AlertType        = "budget_threshold" | "budget_overrun" | "anomaly_detected" | "large_payment" | "duplicate_payment" | "fiscal_year_end" | "sla_breach";

// ── Exercice fiscal ───────────────────────────────────────
export interface FiscalYear {
  id:               string;
  year:             number;
  label:            string;
  start_date:       string;
  end_date:         string;
  status:           FiscalYearStatus;
  status_display:   string;
  total_budget:     number;
  total_paid:       number;
  total_committed:  number;
  consumption_rate: number;
  available_budget: number;
  is_active:        boolean;
  notes:            string;
  closed_at:        string | null;
  created_at:       string;
  updated_at:       string;
}

// ── Budget ────────────────────────────────────────────────
export interface Budget {
  id:                string;
  code:              string;
  label:             string;
  fiscal_year:       string;
  fiscal_year_label: string;
  benefit_type:      string | null;
  benefit_type_name: string;
  department:        string | null;
  department_name:   string;
  status:            BudgetStatus;
  status_display:    string;
  allocated_amount:  number;
  paid_amount:       number;
  committed_amount:  number;
  reserved_amount:   number;
  available_amount:  number;
  consumption_rate:  number;
  is_alert_triggered:boolean;
  is_overrun:        boolean;
  alert_threshold_pct: number;
  approved_by:       string | null;
  approved_by_name:  string | null;
  approved_at:       string | null;
  notes:             string;
  variance_percent:  number | null;
  anomaly_score:     number | null;
  prediction_data:   Record<string, unknown>;
  created_at:        string;
  updated_at:        string;
}

// ── Paiement ──────────────────────────────────────────────
export interface Payment {
  id:                 string;
  reference:          string;
  employee:           string;
  employee_name:      string;
  employee_matricule: string;
  department_name:    string;
  benefit:            string;
  benefit_ref:        string;
  benefit_type_name:  string;
  budget:             string | null;
  budget_code:        string;
  fiscal_year:        string;
  fiscal_year_label:  string;
  amount:             number;
  fees:               number;
  net_amount:         number;
  status:             PaymentStatus;
  status_display:     string;
  payment_method:     PaymentMethod;
  method_display:     string;
  bank_reference:     string;
  bank_account:       string;
  bank_name:          string;
  scheduled_date:     string | null;
  executed_date:      string | null;
  value_date:         string | null;
  approved_by:        string | null;
  approved_by_name:   string | null;
  approved_at:        string | null;
  accounting_entry:   string;
  cost_center:        string;
  notes:              string;
  anomaly_flag:       boolean;
  anomaly_score:      number | null;
  risk_indicators:    Record<string, unknown>;
  created_at:         string;
  updated_at:         string;
  created_by_name:    string | null;
}

// ── Lot de paiements ──────────────────────────────────────
export interface PaymentBatch {
  id:                string;
  reference:         string;
  label:             string;
  fiscal_year:       string;
  fiscal_year_label: string;
  status:            BatchStatus;
  status_display:    string;
  payment_method:    PaymentMethod;
  method_display:    string;
  total_amount:      number;
  payment_count:     number;
  scheduled_date:    string | null;
  executed_date:     string | null;
  bank_reference:    string;
  approved_by:       string | null;
  approved_by_name:  string | null;
  approved_at:       string | null;
  notes:             string;
  created_at:        string;
  updated_at:        string;
}

// ── Écriture comptable ────────────────────────────────────
export interface FinancialEntry {
  id:                 string;
  entry_number:       string;
  entry_type:         EntryType;
  entry_type_display: string;
  label:              string;
  amount:             number;
  entry_date:         string;
  accounting_date:    string;
  debit_account:      string;
  credit_account:     string;
  payment:            string | null;
  budget:             string | null;
  created_by_name:    string;
  notes:              string;
  created_at:         string;
}

// ── Alerte financière ─────────────────────────────────────
export interface FinancialAlert {
  id:                 string;
  alert_type:         AlertType;
  alert_type_display: string;
  severity:           AlertSeverity;
  severity_display:   string;
  title:              string;
  message:            string;
  is_read:            boolean;
  is_resolved:        boolean;
  ai_generated:       boolean;
  ai_confidence:      number | null;
  fiscal_year:        string | null;
  budget:             string | null;
  payment:            string | null;
  created_at:         string;
}

// ── Dashboard data ────────────────────────────────────────
export interface FinanceDashboard {
  fiscal_year: {
    id:               string;
    year:             number;
    label:            string;
    status:           string;
    consumption_rate: number;
    total_budget:     number;
    total_paid:       number;
    total_committed:  number;
    available:        number;
  };
  payments: {
    total_count:   number;
    paid_count:    number;
    pending_count: number;
    total_paid:    number;
    anomaly_count: number;
    by_status:     { status: string; count: number; total: number }[];
  };
  budgets: {
    total_count:     number;
    overrun_count:   number;
    alert_count:     number;
    total_allocated: number;
    total_paid:      number;
  };
  monthly_trend: { month: string; count: number; amount: number }[];
  top_benefit_types: { code: string; name: string; count: number; total: number }[];
  alerts: { alert_type: string; severity: string; title: string; created_at: string }[];
}

// ── Config UI ─────────────────────────────────────────────
export const PAYMENT_STATUS_UI: Record<PaymentStatus, { label: string; badgeClass: string }> = {
  pending:    { label: "En attente",    badgeClass: "bg-amber-100 text-amber-700"  },
  approved:   { label: "Approuvé",      badgeClass: "bg-blue-100 text-blue-700"    },
  processing: { label: "En traitement", badgeClass: "bg-purple-100 text-purple-700"},
  paid:       { label: "Payé",          badgeClass: "bg-green-100 text-green-700"  },
  failed:     { label: "Échoué",        badgeClass: "bg-red-100 text-red-700"      },
  cancelled:  { label: "Annulé",        badgeClass: "bg-gray-100 text-gray-500"    },
  reversed:   { label: "Inversé",       badgeClass: "bg-orange-100 text-orange-700"},
};

export const ALERT_SEVERITY_UI: Record<AlertSeverity, { badgeClass: string; icon: string }> = {
  info:     { badgeClass: "bg-blue-100 text-blue-700",   icon: "ℹ️" },
  warning:  { badgeClass: "bg-amber-100 text-amber-700", icon: "⚠️" },
  critical: { badgeClass: "bg-red-100 text-red-700",     icon: "🚨" },
};

// ── Filtres ───────────────────────────────────────────────
export interface PaymentFilters {
  search?:       string;
  status?:       PaymentStatus | "";
  fiscal_year?:  string;
  budget?:       string;
  department?:   string;
  date_from?:    string;
  date_to?:      string;
  anomaly_only?: boolean;
  ordering?:     string;
  page?:         number;
  page_size?:    number;
}

export interface BudgetFilters {
  fiscal_year?: string;
  benefit_type?:string;
  department?:  string;
  status?:      BudgetStatus | "";
}
