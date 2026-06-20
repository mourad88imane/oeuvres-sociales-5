/**
 * ============================================================
 * AUTH STORE — État d'authentification global (Zustand)
 * ============================================================
 * Gère : tokens JWT, profil utilisateur, état de connexion.
 * Persistance dans sessionStorage (pas localStorage → sécurité).
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { jwtDecode } from "jwt-decode";

// ── Types ──────────────────────────────────────────────────
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "gestionnaire" | "comptable" | "consultant";
  role_display: string;
  must_change_password: boolean;
  avatar: string | null;
  tenant_id?: string | null;
  tenant_name?: string | null;
  preferences?: {
    language: "fr" | "ar";
    theme: "light" | "dark";
    layout_direction: "ltr" | "rtl";
  };
}

interface JwtPayload {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  must_change_password: boolean;
  tenant_id?: string | null;
  exp: number;
}

interface AuthState {
  // État
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setTokens: (accessToken: string, refreshToken: string, userData?: Partial<UserProfile>) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  isTokenExpired: () => boolean;
  hasRole: (...roles: string[]) => boolean;
  canApprove: () => boolean;
  canPay: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // ── État initial ──────────────────────────────────
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,

      // ── Actions ───────────────────────────────────────
      setTokens: (accessToken, refreshToken, userData?: Partial<UserProfile>) => {
        try {
          const payload = jwtDecode<JwtPayload>(accessToken);
          const user: UserProfile = {
            id: userData?.id || payload.user_id,
            email: userData?.email || payload.email,
            full_name: userData?.full_name || payload.full_name,
            role: (userData?.role || payload.role) as UserProfile["role"],
            role_display: userData?.role_display || payload.role,
            must_change_password: userData?.must_change_password ?? payload.must_change_password,
            avatar: userData?.avatar || null,
            tenant_id: userData?.tenant_id || payload.tenant_id || null,
            tenant_name: userData?.tenant_name || null,
            preferences: userData?.preferences || { language: "fr", theme: "light", layout_direction: "ltr" },
          };
          set({ accessToken, refreshToken, user, isAuthenticated: true });
        } catch {
          set({ accessToken, refreshToken, isAuthenticated: true });
        }
      },

      setUser: (user) => set({ user }),

      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),

      setLoading: (isLoading) => set({ isLoading }),

      isTokenExpired: () => {
        const { accessToken } = get();
        if (!accessToken) return true;
        try {
          const { exp } = jwtDecode<JwtPayload>(accessToken);
          // Considérer expiré 30 secondes avant l'expiration réelle
          return Date.now() >= (exp - 30) * 1000;
        } catch {
          return true;
        }
      },

      hasRole: (...roles) => {
        const { user } = get();
        return user ? roles.includes(user.role) : false;
      },

      canApprove: () => {
        const { user } = get();
        return user ? ["admin", "gestionnaire"].includes(user.role) : false;
      },

      canPay: () => {
        const { user } = get();
        return user ? ["admin", "comptable"].includes(user.role) : false;
      },
    }),
    {
      name: "auth-storage",
      // sessionStorage : données effacées à la fermeture du navigateur
      storage: createJSONStorage(() => sessionStorage),
      // Persister uniquement les tokens (pas l'état de chargement)
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
