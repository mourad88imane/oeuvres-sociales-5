export interface DashboardStats {
  total_calls: number;
  errors: number;
  error_rate: number;
  avg_duration_ms: number;
  top_endpoints: { endpoint: string; method: string; count: number; avg_dur: number; err_count: number }[];
  calls_by_hour: { hour: string; count: number }[];
  security_alerts: number;
  degraded_endpoints: number;
  top_users: { user__email: string; count: number }[];
}

export interface APIRequestLogEntry {
  id: string;
  method: string;
  endpoint: string;
  status_code: number;
  duration_ms: number;
  is_error: boolean;
  error_message: string;
  user_email: string;
  ip_address: string;
  request_id: string;
  time_ago: string;
  timestamp: string;
}

export interface SecurityEventEntry {
  id: string;
  event_type: string;
  event_type_display: string;
  severity: string;
  severity_display: string;
  user_email: string;
  user_role: string;
  ip_address: string;
  endpoint: string;
  details: Record<string, unknown>;
  action_taken: string;
  resolved: boolean;
  resolved_at: string | null;
  resolved_by_email: string;
  resolution_note: string;
  time_ago: string;
  timestamp: string;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  action_display: string;
  severity: string;
  severity_display: string;
  user_email: string;
  user_role: string;
  content_type_name: string;
  object_id: string;
  object_repr: string;
  changed_fields: string[] | null;
  ip_address: string;
  endpoint: string;
  request_id: string;
  timestamp: string;
}

export interface AuditStats {
  total: number;
  by_action: { action: string; count: number }[];
  by_severity: { severity: string; count: number }[];
  by_day: { day: string; count: number }[];
  top_users: { user_email: string; count: number }[];
}

export interface EndpointStatus {
  endpoint: string;
  method: string;
  total_calls: number;
  error_count: number;
  error_rate: number;
  avg_duration_ms: number;
  max_duration_ms: number;
  last_called: string | null;
  is_degraded: boolean;
  degraded_since: string | null;
  degraded_duration: string | null;
}
