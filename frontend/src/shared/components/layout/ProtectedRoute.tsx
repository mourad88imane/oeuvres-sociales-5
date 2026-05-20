/**
 * PROTECTED ROUTE — Protection des routes par authentification et rôle
 *
 * Usage :
 *   <ProtectedRoute>                          → authentifié seulement
 *   <ProtectedRoute roles={["admin"]}>        → admin seulement
 *   <ProtectedRoute roles={["admin","gestionnaire"]}>  → OR logic
 */
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@modules/auth/store/authStore";

interface ProtectedRouteProps {
  /** Rôles autorisés. Si vide → tout utilisateur authentifié. */
  roles?: string[];
  /** Redirection si non autorisé (défaut : /login) */
  redirectTo?: string;
}

export function ProtectedRoute({
  roles = [],
  redirectTo = "/login",
}: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, user } = useAuthStore();

  // 1. Non authentifié → login
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // 2. Authentifié mais rôle insuffisant → accueil ou page 403
  if (roles.length > 0 && user && !roles.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }

  // 3. Doit changer son mot de passe → forcer le changement
  if (user?.must_change_password && location.pathname !== "/change-password") {
    return <Navigate to="/change-password" replace />;
  }

  return <Outlet />;
}

// ── HOC version (alternative) ────────────────────────────
interface RoleGuardProps {
  children: React.ReactNode;
  roles: string[];
  fallback?: React.ReactNode;
}

/**
 * RoleGuard — Affiche les enfants uniquement si le rôle correspond.
 * Utile pour masquer des boutons ou sections dans une page.
 *
 * Usage :
 *   <RoleGuard roles={["admin"]}>
 *     <button>Supprimer</button>
 *   </RoleGuard>
 */
export function RoleGuard({ children, roles, fallback = null }: RoleGuardProps) {
  const { user } = useAuthStore();
  if (!user || !roles.includes(user.role)) return <>{fallback}</>;
  return <>{children}</>;
}
