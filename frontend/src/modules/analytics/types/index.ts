export type KpiCategory = "hr" | "finance" | "benefits" | "conventions" | "global";
export type TrendDirection = "up" | "down" | "stable";
export type ReportCategory = "employees" | "benefits" | "finance" | "conventions" | "kpi" | "custom";
export type ExportFormat = "excel" | "csv" | "pdf" | "json";
export type ExportStatus = "pending" | "processing" | "completed" | "failed";
export type WidgetType = "kpi_summary" | "kpi_card" | "chart_bar" | "chart_line" | "chart_pie" | "chart_donut" | "table" | "list" | "alert_feed" | "stat_card" | "custom";
export type PeriodFilter = "7d" | "30d" | "90d" | "6m" | "1y" | "all";

export interface KpiValue {
  id: string;
  code: string;
  name: string;
  description: string;
  category: KpiCategory;
  unit: string;
  target_value: number | null;
  current_value: number | null;
  previous_value: number | null;
  variation: number | null;
  date: string | null;
  trend: TrendDirection;
}

export interface MonthlyTrend {
  month: string;
  date: string;
  benefits_count: number;
  benefits_amount: number;
  payments_count: number;
  payments_amount: number;
  conventions_created: number;
}

export interface GlobalStats {
  employees: {
    total: number;
    active: number;
    new_this_month: number;
    by_department: { department__name: string; count: number }[];
    by_wilaya: { wilaya: string; count: number }[];
  };
  beneficiaries: {
    total: number;
    active: number;
    new_this_month: number;
  };
  benefits: {
    total: number;
    pending: number;
    approved: number;
    paid: number;
    rejected: number;
    total_amount: number;
    month_amount: number;
    by_type: { benefit_type__name: string; count: number; total: number }[];
  };
  conventions: {
    total: number;
    active: number;
    expiring_soon: number;
    expired: number;
  };
  finance: {
    total_budget: number;
    total_paid: number;
    pending_payments: number;
    month_paid: number;
  };
}

export interface TopStats {
  top_benefit_types: { benefit_type__name: string; benefit_type__code: string; count: number; total: number }[];
  top_departments_by_benefits: { employee__department__name: string; count: number; total: number }[];
  top_employees_by_amount: { employee__full_name: string; employee__matricule: string; count: number; total: number }[];
  top_partners: { partner__name: string; partner__code: string; count: number; total: number }[];
}

export interface GlobalDashboardData {
  kpis: KpiValue[];
  summary: GlobalStats;
  trends: MonthlyTrend[];
  top: TopStats;
  date: string;
}

export interface KpiHistory {
  id: string;
  kpi: string;
  kpi_code: string;
  kpi_name: string;
  kpi_unit: string;
  value: number;
  date: string;
  previous_value: number | null;
  variation: number | null;
  created_at: string;
}

export interface ReportDefinition {
  id: string;
  code: string;
  title: string;
  description: string;
  category: ReportCategory;
  category_display: string;
  default_format: ExportFormat;
  filters_config: Record<string, unknown>;
  columns_config: unknown[];
  chart_config: Record<string, unknown>;
  is_system: boolean;
  is_active: boolean;
  ai_insights_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataExport {
  id: string;
  report: string | null;
  report_title: string | null;
  export_format: ExportFormat;
  status: ExportStatus;
  status_display: string;
  file: string | null;
  download_url: string | null;
  file_size: number;
  filters_used: Record<string, unknown>;
  row_count: number;
  error_message: string;
  completed_at: string | null;
  duration_ms: number;
  created_at: string;
  created_by_name: string | null;
}

export interface DashboardWidget {
  id: string;
  user: string | null;
  title: string;
  widget_type: WidgetType;
  widget_type_display: string;
  size: "sm" | "md" | "lg" | "xl" | "full";
  size_display: string;
  config: Record<string, unknown>;
  is_global: boolean;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const TREND_UI: Record<TrendDirection, { label: string; icon: string; class: string }> = {
  up:     { label: "En hausse", icon: "📈", class: "text-green-600" },
  down:   { label: "En baisse", icon: "📉", class: "text-red-600" },
  stable: { label: "Stable",    icon: "➡️", class: "text-gray-500" },
};

export const KPI_CATEGORY_UI: Record<KpiCategory, { label: string; color: string }> = {
  hr:          { label: "Ressources Humaines", color: "#1A3C6E" },
  finance:     { label: "Finance",             color: "#10B981" },
  benefits:    { label: "Prestations",         color: "#F59E0B" },
  conventions: { label: "Conventions",         color: "#8B5CF6" },
  global:      { label: "Global",              color: "#06B6D4" },
};

export interface AnalyticsFilter {
  date_from?: string;
  date_to?: string;
  period?: PeriodFilter;
  category?: string;
  months?: number;
  limit?: number;
}
