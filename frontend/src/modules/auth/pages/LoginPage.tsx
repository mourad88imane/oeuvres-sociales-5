/**
 * PAGE LOGIN — Formulaire de connexion
 */
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AlertCircle, LogIn, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useAuthStore } from "../store/authStore";
import { makeZodI18nMap } from "@shared/utils/zod-i18n";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login, isLoggingIn, loginError } = useAuth();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema, { errorMap: makeZodI18nMap(t) }),
  });

  // Rediriger si déjà connecté
  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true });
  }, [isAuthenticated, navigate]);

  const onSubmit = (data: LoginFormData) => {
    login(data);
  };

  const getErrorMessage = () => {
    if (!loginError) return null;
    const err = loginError as { response?: { data?: { message?: string; code?: string } } };
    if (err.response?.data?.code === "ACCOUNT_LOCKED") {
      return t("auth.errorLocked");
    }
    return err.response?.data?.message || t("auth.errorInvalid");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand to-brand-light flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo / En-tête */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <svg className="w-9 h-9 text-brand" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">{t("app.name")}</h1>
          <p className="text-blue-200 text-sm mt-1">{t("app.tagline")}</p>
        </div>

        {/* Carte de connexion */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">{t("auth.loginTitle")}</h2>

          {/* Erreur globale */}
          {loginError && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4 mb-5">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
              <p className="text-sm text-red-700">{getErrorMessage()}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                {t("auth.email")}
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                className={`w-full px-4 py-2.5 border rounded-lg text-sm transition-colors
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                  ${errors.email ? "border-red-400 bg-red-50" : "border-gray-300 bg-white"}`}
                placeholder={t("auth.emailPlaceholder")}
              />
              {errors.email && (
                <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
              )}
            </div>

            {/* Mot de passe */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
                {t("auth.password")}
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  {...register("password")}
                  className={`w-full px-4 py-2.5 pr-11 border rounded-lg text-sm transition-colors
                    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                    ${errors.password ? "border-red-400 bg-red-50" : "border-gray-300 bg-white"}`}
                  placeholder={t("auth.passwordPlaceholder")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Bouton submit */}
            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full flex items-center justify-center gap-2 bg-brand hover:bg-brand-light
                text-white font-medium py-2.5 px-4 rounded-lg transition-colors
                disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {isLoggingIn ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  {t("auth.loggingIn")}
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  {t("auth.loginButton")}
                </>
              )}
            </button>
          </form>
        </div>

        {isAuthenticated && user?.tenant_name && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
            <p className="text-xs text-blue-600">
              {user.tenant_name}
            </p>
          </div>
        )}

        <p className="text-center text-blue-200 text-xs mt-6">
          {t("app.copyright", { year: new Date().getFullYear() })}
        </p>
      </div>
    </div>
  );
}
