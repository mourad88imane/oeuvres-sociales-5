import apiClient from "@shared/api/apiClient";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Notification, UnreadCount, NotificationPreferences, MarkReadResponse } from "../types";

interface NotificationFilters {
  page?: number;
  is_read?: string;
  priority?: string;
  channel?: string;
}

interface PaginatedNotifications {
  count: number;
  next: string | null;
  previous: string | null;
  results: Notification[];
}

export const notificationsApi = {
  list: (params: NotificationFilters = {}) =>
    apiClient.get<PaginatedNotifications>("/notifications/", { params }),
  unreadCount: () =>
    apiClient.get<{ status: string; data: UnreadCount }>("/notifications/unread_count/"),
  markRead: (ids: string[]) =>
    apiClient.post<MarkReadResponse>("/notifications/mark_read/", { ids }),
  markAllRead: () =>
    apiClient.post<MarkReadResponse>("/notifications/mark_read/", { all: true }),
  markOneRead: (id: string) =>
    apiClient.post(`/notifications/${id}/mark_one_read/`),
  getPreferences: () =>
    apiClient.get<{ status: string; data: NotificationPreferences }>("/notifications/preferences/my_preferences/"),
  updatePreferences: (data: Partial<NotificationPreferences>) =>
    apiClient.patch<{ status: string; data: NotificationPreferences }>(
      "/notifications/preferences/my_preferences/", data
    ),
};

export const NOTIFICATION_KEYS = {
  all:      () => ["notifications"] as const,
  list:     (f?: NotificationFilters) => ["notifications", "list", f] as const,
  count:    () => ["notifications", "count"] as const,
  prefs:    () => ["notifications", "prefs"] as const,
};

export function useNotifications(filters: NotificationFilters = {}) {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.list(filters),
    queryFn: () => notificationsApi.list(filters).then(r => r.data),
    placeholderData: (prev) => prev,
  });
}

export function useUnreadCount(poll = true) {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.count(),
    queryFn: () => notificationsApi.unreadCount().then(r => r.data.data),
    refetchInterval: poll ? 15000 : false,
    staleTime: 10000,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ids: string[]) => notificationsApi.markRead(ids),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all() });
    },
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all() });
    },
  });
}

export function useMarkOneRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notificationsApi.markOneRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATION_KEYS.all() });
    },
  });
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: NOTIFICATION_KEYS.prefs(),
    queryFn: () => notificationsApi.getPreferences().then(r => r.data.data),
    staleTime: 1000 * 60 * 5,
  });
}

export function useUpdatePreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<NotificationPreferences>) =>
      notificationsApi.updatePreferences(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: NOTIFICATION_KEYS.prefs() });
    },
  });
}
