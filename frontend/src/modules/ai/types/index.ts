export interface AIAnomaly {
  id: string;
  detection_method: string;
  severity: "low" | "medium" | "high" | "critical";
  severity_display: string;
  status: "new" | "confirmed" | "false_positive" | "investigating" | "resolved";
  status_display: string;
  target_type: string;
  target_id: string;
  target_repr: string;
  metric_name: string;
  expected_value: number | null;
  actual_value: number | null;
  deviation: number | null;
  deviation_pct: number | null;
  explanation: string;
  created_at: string;
  time_ago: string;
}

export interface AIRecommendation {
  id: string;
  domain: string;
  priority: "low" | "medium" | "high" | "critical";
  priority_display: string;
  title: string;
  detail: string;
  action_url: string;
  action_label: string;
  confidence: number | null;
  feedback: "pending" | "helpful" | "not_helpful" | "applied" | "dismissed";
  feedback_display: string;
  is_active: boolean;
  created_at: string;
  time_ago: string;
}

export interface AIScore {
  id: string;
  score_type: string;
  target_type: string;
  target_id: string;
  target_repr: string;
  score: number;
  confidence: number | null;
  feature_importance: Record<string, number>;
  explanation: string;
  recommendation: string;
  created_at: string;
}

export interface AssistantResponse {
  query: string;
  intent: string;
  entities: Record<string, unknown>;
  response: {
    text: string;
    type: string;
    data?: Record<string, unknown>;
    suggestions?: string[];
  };
}

export interface AssistantQuery {
  query: string;
}

export interface DetectionResult {
  kpi_anomalies?: AIAnomaly[];
  benefit_anomalies?: AIAnomaly[];
  payment_anomalies?: AIAnomaly[];
}

export interface ForecastData {
  target: string;
  fiscal_year: number;
  total_budget: number;
  method: string;
  horizon_months: number;
  historical_months: number;
  forecasts: Record<string, {
    method: string;
    horizon: number;
    forecasts: { step: number; value: number; n_models?: number }[];
    r_squared?: number;
    slope?: number;
  }>;
}

export interface WhatIfData {
  scenario: Record<string, number>;
  impact: {
    budget_change: string;
    new_annual_cost: number;
  };
  adjusted_forecasts: {
    step: number;
    base: number;
    adjusted: number;
  }[];
}

export interface MedicalDocumentAnalysisResult {
  id: string;
  title: string;
  category: string;
  category_display: string;
  extracted_text: string;
  ocr_confidence: number | null;
  medical_keywords: string[];
  diagnosis_mentions: string[];
  medication_mentions: string[];
  summary: string;
  language: string;
  file_name: string;
  file_size_bytes: number;
  file_type: string;
  page_count: number | null;
  analysis_duration_ms: number;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
  time_ago: string;
}
