/**
 * SIDEBAR — Navigation principale
 * S'adapte aux rôles : affiche uniquement les sections autorisées.
 */
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Users, UserCheck, Gift, Wallet,
  FileText, BarChart3, Settings, LogOut, ChevronLeft,
  Building2, Shield, Lightbulb, Activity, Bot,
} from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "@modules/auth/hooks/useAuth";
import { useAuthStore } from "@modules/auth/store/authStore";

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
  roles?: string[];      // Si vide → tous les rôles
  badge?: number;
}

const navItems: NavItem[] = [
  {
    label: "Tableau de bord",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Employés",
    path: "/employees",
    icon: Users,
    roles: ["admin", "gestionnaire", "comptable"],
  },
  {
    label: "Ayants droit",
    path: "/beneficiaries",
    icon: UserCheck,
    roles: ["admin", "gestionnaire"],
  },
  {
    label: "Prestations",
    path: "/benefits",
    icon: Gift,
  },
  {
    label: "Finance",
    path: "/finance",
    icon: Wallet,
    roles: ["admin", "comptable"],
  },
  {
    label: "Conventions",
    path: "/conventions",
    icon: Building2,
    roles: ["admin", "gestionnaire", "comptable"],
  },
  {
    label: "Rapports",
    path: "/reporting",
    icon: FileText,
    roles: ["admin", "gestionnaire", "comptable"],
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: BarChart3,
    roles: ["admin"],
  },
  {
    label: "Décisions IA",
    path: "/analytics/decisions",
    icon: Lightbulb,
    roles: ["admin"],
  },
  {
    label: "Assistant IA",
    path: "/ai/assistant",
    icon: Bot,
    roles: ["admin"],
  },
  {
    label: "Monitoring",
    path: "/monitoring",
    icon: Activity,
    roles: ["admin"],
  },
];

const adminItems: NavItem[] = [
  {
    label: "Utilisateurs",
    path: "/users",
    icon: Shield,
    roles: ["admin"],
  },
  {
    label: "Paramètres",
    path: "/settings",
    icon: Settings,
    roles: ["admin"],
  },
];

interface SidebarProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

export function Sidebar({ collapsed = false, onCollapse }: SidebarProps) {
  const { logout } = useAuth();
  const { user } = useAuthStore();

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
                  Administration
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
          {!collapsed && <span>Déconnexion</span>}
        </button>
      </div>
    </aside>
  );
}

// ── Composant NavItem ──────────────────────────────────────
function NavItem({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
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
      title={collapsed ? item.label : undefined}
    >
      <item.icon className="w-5 h-5 shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
      {!collapsed && item.badge != null && item.badge > 0 && (
        <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center">
          {item.badge > 99 ? "99+" : item.badge}
        </span>
      )}
    </NavLink>
  );
}
