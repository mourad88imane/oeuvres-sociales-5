import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api";
import { useAuthStore } from "../store/authStore";

export function ChangePasswordPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [form, setForm] = useState({ old_password: "", new_password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!user?.must_change_password) {
    navigate("/dashboard", { replace: true });
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (form.new_password !== form.confirm_password) {
      setError(t("auth.passwords_dont_match", "Les mots de passe ne correspondent pas"));
      return;
    }
    if (form.new_password.length < 8) {
      setError(t("auth.password_too_short", "Le mot de passe doit contenir au moins 8 caractères"));
      return;
    }

    setLoading(true);
    try {
      await authApi.changePassword({
        old_password: form.old_password,
        new_password: form.new_password,
        confirm_password: form.confirm_password,
      });
      setUser({ ...user, must_change_password: false });
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      const data = err?.response?.data;
      const msg = data?.detail || data?.old_password?.[0] || data?.new_password?.[0] || data?.confirm_password?.[0] || data?.non_field_errors?.[0] || t("auth.change_password_error", "Erreur lors du changement de mot de passe");
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
        <h1 className="text-2xl font-bold text-center mb-2">
          {t("auth.change_password_title", "Changer le mot de passe")}
        </h1>
        <p className="text-gray-500 text-center mb-6">
          {t("auth.change_password_subtitle", "Vous devez changer votre mot de passe avant de continuer.")}
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t("auth.current_password", "Mot de passe actuel")}
            </label>
            <input
              type="password"
              value={form.old_password}
              onChange={(e) => setForm({ ...form, old_password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t("auth.new_password", "Nouveau mot de passe")}
            </label>
            <input
              type="password"
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t("auth.confirm_new_password", "Confirmer le nouveau mot de passe")}
            </label>
            <input
              type="password"
              value={form.confirm_password}
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition disabled:opacity-50"
          >
            {loading ? t("common.loading", "Chargement...") : t("auth.change_password_btn", "Changer le mot de passe")}
          </button>
        </form>
      </div>
    </div>
  );
}
