/**
 * AUTH API — Appels API d'authentification
 */
import apiClient from "@shared/api/apiClient";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  status: string;
  message: string;
  access: string;
  refresh: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    role_display: string;
    must_change_password: boolean;
    avatar: string | null;
  };
}

export const authApi = {
  login: (credentials: LoginCredentials) =>
    apiClient.post<LoginResponse>("/auth/login/", credentials),

  logout: (refreshToken: string) =>
    apiClient.post("/auth/logout/", { refresh: refreshToken }),

  refreshToken: (refresh: string) =>
    apiClient.post("/auth/token/refresh/", { refresh }),

  getMe: () => apiClient.get("/auth/me/"),

  verifyToken: () => apiClient.get("/auth/verify/"),

  changePassword: (data: {
    old_password: string;
    new_password: string;
    confirm_password: string;
  }) => apiClient.post("/users/change-password/", data),
};
