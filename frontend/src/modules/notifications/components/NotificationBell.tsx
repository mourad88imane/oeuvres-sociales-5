import { useState, useRef, useEffect } from "react";
import { Bell, CheckCheck, AlertTriangle, Info, MessageSquare, X } from "lucide-react";
import { clsx } from "clsx";
import { useNavigate } from "react-router-dom";
import { useNotifications, useUnreadCount, useMarkRead, useMarkAllRead } from "../api/index";
import { Spinner } from "@shared/components/ui/index";
import type { Notification } from "../types";

const PRIORITY_ICONS: Record<string, React.ElementType> = {
  critical: AlertTriangle,
  high: AlertTriangle,
  medium: Info,
  low: MessageSquare,
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: "text-red-500 bg-red-50",
  high: "text-orange-500 bg-orange-50",
  medium: "text-blue-500 bg-blue-50",
  low: "text-gray-500 bg-gray-100",
};

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data: unread } = useUnreadCount(true);
  const { data: notifsData, isLoading } = useNotifications({ page: 1, is_read: "false" });
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  const notifications = notifsData?.results ?? [];

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleClick = (n: Notification) => {
    if (!n.is_read) markRead.mutate([n.id]);
    if (n.action_url) navigate(n.action_url);
    setOpen(false);
  };

  const handleMarkAll = () => {
    markAllRead.mutate();
  };

  const count = unread?.count ?? 0;
  const hasPriority = (unread?.high_priority ?? 0) > 0;

  return (
    <div ref={dropdownRef} className="relative">
      <button onClick={() => setOpen(!open)}
        className={clsx("relative p-2 rounded-lg transition-colors", open ? "bg-gray-100" : "hover:bg-gray-100")}>
        <Bell className={clsx("w-5 h-5", hasPriority ? "text-red-500" : "text-gray-600")} />
        {count > 0 && (
          <span className={clsx(
            "absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center",
            "text-[10px] font-bold text-white rounded-full px-1",
            hasPriority ? "bg-red-500" : "bg-gray-400",
          )}>
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-gray-200 z-50 max-h-[70vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-2">
              {count > 0 && (
                <button onClick={handleMarkAll}
                  className="flex items-center gap-1 text-xs text-brand hover:underline">
                  <CheckCheck className="w-3 h-3" /> Tout marquer lu
                </button>
              )}
              <button onClick={() => setOpen(false)} className="p-0.5 text-gray-400 hover:text-gray-600">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Scrollable list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center py-8"><Spinner /></div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center py-10 text-gray-400">
                <Bell className="w-8 h-8 mb-2 opacity-30" />
                <p className="text-sm">Aucune notification</p>
              </div>
            ) : (
              notifications.map(n => {
                const Icon = PRIORITY_ICONS[n.priority] || Info;
                const color = PRIORITY_COLORS[n.priority] || PRIORITY_COLORS.low;
                return (
                  <button key={n.id} onClick={() => handleClick(n)}
                    className={clsx(
                      "w-full text-left px-4 py-3 flex items-start gap-3 transition-colors border-b border-gray-50 last:border-0",
                      n.is_read ? "hover:bg-gray-50" : "bg-blue-50/40 hover:bg-blue-50",
                    )}>
                    <div className={clsx("p-1.5 rounded-lg shrink-0", color)}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={clsx("text-sm truncate", n.is_read ? "text-gray-600" : "text-gray-900 font-medium")}>
                        {n.title}
                      </p>
                      {n.body && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.body}</p>
                      )}
                      <p className="text-[11px] text-gray-400 mt-1">{n.time_ago}</p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
