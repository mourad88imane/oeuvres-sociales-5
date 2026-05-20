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
  intent: string;
  response: string;
  suggestions?: string[];
  data?: Record<string, unknown>;
}

export interface AssistantQuery {
  query: string;
}

export interface DetectionResult {
  kpi_anomalies?: AIAnomaly[];
  benefit_anomalies?: AIAnomaly[];
  payment_anomalies?: AIAnomaly[];
}
