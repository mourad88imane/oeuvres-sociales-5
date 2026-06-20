import { useState, useRef, useEffect } from "react";
import { Bell, CheckCheck, AlertTriangle, Info, MessageSquare, X } from "lucide-react";
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

const PRIORITY_COLORS: Record<string, { color: string; bg: string }> = {
  critical: { color: "#dc2626", bg: "rgba(239,68,68,0.1)" },
  high: { color: "#d97706", bg: "rgba(245,158,11,0.1)" },
  medium: { color: "#3b82f6", bg: "rgba(59,130,246,0.1)" },
  low: { color: "#8a8882", bg: "rgba(138,136,130,0.08)" },
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
        className="relative p-2 rounded-xl transition-colors"
        style={{
          background: open ? "rgba(0,0,0,0.04)" : "transparent",
        }}
        onMouseEnter={e => { e.currentTarget.style.background = "rgba(0,0,0,0.03)"; }}
        onMouseLeave={e => { e.currentTarget.style.background = open ? "rgba(0,0,0,0.04)" : "transparent"; }}
      >
        <Bell className="w-5 h-5" style={{ color: hasPriority ? "#dc2626" : "#8a8882" }} />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center text-[10px] font-bold text-white rounded-full px-1"
            style={{ background: hasPriority ? "#dc2626" : "#ffda2d" }}>
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 z-50 max-h-[70vh] flex flex-col overflow-hidden rounded-[24px]"
          style={{
            background: "#ffffff",
            border: "1px solid rgba(0,0,0,0.06)",
            boxShadow: "0 10px 40px -8px rgba(0,0,0,0.08)",
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid rgba(0,0,0,0.04)" }}>
            <h3 className="text-sm font-bold" style={{ color: "#1a1917" }}>Notifications</h3>
            <div className="flex items-center gap-2">
              {count > 0 && (
                <button onClick={handleMarkAll}
                  className="flex items-center gap-1 text-xs font-bold hover:underline"
                  style={{ color: "#ffda2d" }}>
                  <CheckCheck className="w-3 h-3" /> Tout marquer lu
                </button>
              )}
              <button onClick={() => setOpen(false)} className="p-0.5" style={{ color: "#a8a49a" }}>
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Scrollable list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center py-8"><Spinner /></div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center py-10" style={{ color: "#8a8882" }}>
                <Bell className="w-8 h-8 mb-2 opacity-30" />
                <p className="text-sm font-medium">Aucune notification</p>
              </div>
            ) : (
              notifications.map(n => {
                const Icon = PRIORITY_ICONS[n.priority] || Info;
                const pc = PRIORITY_COLORS[n.priority] || PRIORITY_COLORS.low;
                return (
                  <button key={n.id} onClick={() => handleClick(n)}
                    className="w-full text-left px-4 py-3 flex items-start gap-3 transition-colors"
                    style={{
                      borderBottom: "1px solid rgba(0,0,0,0.04)",
                      background: n.is_read ? "transparent" : "rgba(255,218,45,0.06)",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = "rgba(0,0,0,0.03)"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = n.is_read ? "transparent" : "rgba(255,218,45,0.06)"; }}
                  >
                    <div className="p-1.5 rounded-xl shrink-0" style={{ background: pc.bg }}>
                      <Icon className="w-4 h-4" style={{ color: pc.color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold truncate" style={{ color: n.is_read ? "#8a8882" : "#1a1917" }}>
                        {n.title}
                      </p>
                      {n.body && (
                        <p className="text-xs mt-0.5 line-clamp-2 font-medium" style={{ color: "#8a8882" }}>{n.body}</p>
                      )}
                      <p className="text-[11px] mt-1 font-medium" style={{ color: "#a8a49a" }}>{n.time_ago}</p>
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
