export interface Notification {
  id: string;
  title: string;
  body: string;
  channel: string;
  channel_display: string;
  priority: string;
  priority_display: string;
  is_read: boolean;
  read_at: string | null;
  action_url: string;
  icon: string;
  content_type: number | null;
  object_id: string | null;
  metadata: Record<string, unknown>;
  time_ago: string;
  created_at: string;
}

export interface UnreadCount {
  count: number;
  high_priority: number;
}

export interface NotificationPreferences {
  id: string;
  email_alerts: boolean;
  sms_alerts: boolean;
  push_alerts: boolean;
  digest_frequency: "instant" | "daily" | "weekly";
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
}

export interface MarkReadResponse {
  status: string;
  marked_read: number;
}
