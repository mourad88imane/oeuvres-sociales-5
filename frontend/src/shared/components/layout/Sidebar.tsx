/**
 * SIDEBAR — Navigation principale
 * S'adapte aux rôles : affiche uniquement les sections autorisées.
 */
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Users, UserCheck, Gift, Wallet,
  FileText, BarChart3, Settings, LogOut, ChevronLeft,
  Building2, Shield, Lightbulb, Activity, Bot, Languages,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "@modules/auth/hooks/useAuth";
import { useAuthStore } from "@modules/auth/store/authStore";
import { LanguageSwitcher } from "@shared/components/ui/LanguageSwitcher";

interface NavItem {
  labelKey: string;
  path: string;
  icon: React.ElementType;
  roles?: string[];      // Si vide → tous les rôles
  badge?: number;
}

const navItemDefs: Omit<NavItem, "labelKey">[] = [
  { path: "/dashboard", icon: LayoutDashboard },
  {
    path: "/employees",
    icon: Users,
    roles: ["admin", "gestionnaire", "comptable"],
  },
  {
    path: "/beneficiaries",
    icon: UserCheck,
    roles: ["admin", "gestionnaire"],
  },
  { path: "/benefits", icon: Gift },
  {
    path: "/finance",
    icon: Wallet,
    roles: ["admin", "comptable"],
  },
  {
    path: "/conventions",
    icon: Building2,
    roles: ["admin", "gestionnaire", "comptable"],
  },
  {
    path: "/reporting",
    icon: FileText,
    roles: ["admin", "gestionnaire", "comptable"],
  },
  {
    path: "/analytics",
    icon: BarChart3,
    roles: ["admin"],
  },
  {
    path: "/analytics/decisions",
    icon: Lightbulb,
    roles: ["admin"],
  },
  {
    path: "/ai/assistant",
    icon: Bot,
    roles: ["admin"],
  },
  {
    path: "/monitoring",
    icon: Activity,
    roles: ["admin"],
  },
];

const adminItemDefs: Omit<NavItem, "labelKey">[] = [
  { path: "/users", icon: Shield, roles: ["admin"] },
  { path: "/settings", icon: Settings, roles: ["admin"] },
];

const pathToNavKey: Record<string, string> = {
  "/dashboard": "dashboard",
  "/employees": "employees",
  "/beneficiaries": "beneficiaries",
  "/benefits": "benefits",
  "/finance": "finance",
  "/conventions": "conventions",
  "/reporting": "reports",
  "/analytics": "analytics",
  "/analytics/decisions": "decisions",
  "/ai/assistant": "assistant",
  "/monitoring": "monitoring",
  "/users": "users",
  "/settings": "settings",
};

interface SidebarProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

export function Sidebar({ collapsed = false, onCollapse }: SidebarProps) {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const { user } = useAuthStore();

  const navItems: NavItem[] = navItemDefs.map((d) => ({
    ...d,
    labelKey: pathToNavKey[d.path],
  }));

  const adminItems: NavItem[] = adminItemDefs.map((d) => ({
    ...d,
    labelKey: pathToNavKey[d.path],
  }));

  const filteredNavItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  const filteredAdminItems = adminItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <aside
      className={clsx(
        "flex flex-col h-full bg-brand text-white transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* ── Logo ──────────────────────────────────────── */}
      <div className="flex items-center justify-between p-4 border-b border-blue-800">
        {!collapsed && (
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-brand" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <div>
              <p className="font-bold text-sm leading-tight">Oeuvres</p>
              <p className="text-blue-300 text-xs">Sociales</p>
            </div>
          </div>
        )}
        <button
          onClick={() => onCollapse?.(!collapsed)}
          className="p-1 rounded-lg hover:bg-blue-800 transition-colors"
        >
          <ChevronLeft
            className={clsx("w-4 h-4 transition-transform", collapsed && "rotate-180")}
          />
        </button>
      </div>

      {/* ── Navigation principale ──────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {filteredNavItems.map((item) => (
          <NavItem key={item.path} item={item} collapsed={collapsed} />
        ))}

        {/* ── Section Admin ────────────────────────────── */}
        {filteredAdminItems.length > 0 && (
          <>
            {!collapsed && (
              <div className="px-3 pt-4 pb-1">
                <p className="text-blue-400 text-xs font-semibold uppercase tracking-wider">
                  {t("nav.administration")}
                </p>
              </div>
            )}
            <div className="border-t border-blue-800 pt-2">
              {filteredAdminItems.map((item) => (
                <NavItem key={item.path} item={item} collapsed={collapsed} />
              ))}
            </div>
          </>
        )}
      </nav>

      {/* ── Langue ─────────────────────────────────────── */}
      {!collapsed && (
        <div className="border-t border-blue-800 p-3">
          <div className="flex items-center gap-2 mb-2 px-1">
            <Languages className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-blue-400 text-xs font-semibold uppercase tracking-wider">Langue</span>
          </div>
          <LanguageSwitcher />
        </div>
      )}

      {/* ── Profil utilisateur ─────────────────────────── */}
      <div className="border-t border-blue-800 p-3">
        {!collapsed ? (
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold shrink-0">
              {user?.full_name?.charAt(0).toUpperCase() || "?"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-blue-300 text-xs truncate">{user?.role_display}</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center mb-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold">
              {user?.full_name?.charAt(0).toUpperCase() || "?"}
            </div>
          </div>
        )}
        <button
          onClick={() => logout()}
          className={clsx(
            "flex items-center gap-2 w-full px-2 py-1.5 rounded-lg",
            "text-blue-300 hover:text-white hover:bg-red-600/20 transition-colors text-sm",
            collapsed && "justify-center"
          )}
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span>{t("auth.logout")}</span>}
        </button>
      </div>
    </aside>
  );
}

// ── Composant NavItem ──────────────────────────────────────
function NavItem({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const { t } = useTranslation();
  const label = t(`nav.${item.labelKey}`, item.labelKey);
  return (
    <NavLink
      to={item.path}
      className={({ isActive }) =>
        clsx(
          "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm",
          collapsed && "justify-center px-2",
          isActive
            ? "bg-white/20 text-white font-medium"
            : "text-blue-200 hover:bg-white/10 hover:text-white"
        )
      }
      title={collapsed ? label : undefined}
    >
      <item.icon className="w-5 h-5 shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
      {!collapsed && item.badge != null && item.badge > 0 && (
        <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center">
          {item.badge > 99 ? "99+" : item.badge}
        </span>
      )}
    </NavLink>
  );
}
