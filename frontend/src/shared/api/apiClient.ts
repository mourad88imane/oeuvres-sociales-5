/**
 * ============================================================
 * AXIOS CLIENT — Instance configurée avec intercepteurs JWT
 * ============================================================
 * - Injecte automatiquement le token Bearer dans chaque requête
 * - Rafraîchit automatiquement le token expiré (rotation)
 * - Redirige vers /login si le refresh échoue
 * - Ajoute X-Request-ID pour la corrélation des logs
 */
import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from "axios";
import { v4 as uuidv4 } from "uuid";
import { useAuthStore } from "@modules/auth/store/authStore";

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || "/api/v1";

// ── Instance principale ────────────────────────────────────
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ── Instance séparée pour le refresh (évite la boucle infinie) ──
const refreshClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
});

// ── Flag pour éviter les refresh simultanés ────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token!);
    }
  });
  failedQueue = [];
};

// ── Intercepteur de requête ────────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Injecter le token JWT
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Ajouter un ID unique par requête (corrélation logs)
    config.headers["X-Request-ID"] = uuidv4();

    return config;
  },
  (error) => Promise.reject(error)
);

// ── Intercepteur de réponse (refresh automatique) ─────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Si 401 et pas déjà en train de retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = useAuthStore.getState().refreshToken;

      // Pas de refresh token → déconnexion
      if (!refreshToken) {
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      // Mettre en file les requêtes pendant le refresh
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await refreshClient.post("/auth/token/refresh/", {
          refresh: refreshToken,
        });

        const { access, refresh } = response.data;

        // Mettre à jour le store
        useAuthStore.getState().setTokens(access, refresh);

        // Relancer les requêtes en attente
        processQueue(null, access);

        // Relancer la requête originale
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
