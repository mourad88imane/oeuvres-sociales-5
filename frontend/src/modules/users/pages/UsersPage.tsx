/**
 * USERS PAGE — Gestion des utilisateurs (admin seulement)
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, Search, UserX, UserCheck, Edit2 } from "lucide-react";

interface UserItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  last_login: string | null;
  date_joined: string;
}

const ROLE_CONFIG: Record<string, { labelKey: string; classes: string }> = {
  admin:        { labelKey: "users.admin",        classes: "bg-red-100 text-red-700" },
  gestionnaire: { labelKey: "users.gestionnaire", classes: "bg-blue-100 text-blue-700" },
  comptable:    { labelKey: "users.comptable",    classes: "bg-purple-100 text-purple-700" },
  consultant:   { labelKey: "users.consultant",   classes: "bg-gray-100 text-gray-700" },
};

const MOCK_USERS: UserItem[] = [
  { id: "1", email: "admin@oeuvres.dz",        full_name: "Administrateur Système", role: "admin",        is_active: true,  last_login: "2024-12-05T09:30:00Z", date_joined: "2023-01-15" },
  { id: "2", email: "gestionnaire@oeuvres.dz", full_name: "Amina Bensalem",         role: "gestionnaire", is_active: true,  last_login: "2024-12-04T14:22:00Z", date_joined: "2023-03-20" },
  { id: "3", email: "comptable@oeuvres.dz",    full_name: "Karim Taleb",            role: "comptable",    is_active: true,  last_login: "2024-12-05T08:15:00Z", date_joined: "2023-02-10" },
  { id: "4", email: "consultant@oeuvres.dz",   full_name: "Leila Ferhat",           role: "consultant",   is_active: true,  last_login: "2024-12-01T11:00:00Z", date_joined: "2023-06-01" },
  { id: "5", email: "inactive@oeuvres.dz",     full_name: "Ahmed Inactif",          role: "gestionnaire", is_active: false, last_login: "2024-10-10T09:00:00Z", date_joined: "2022-11-01" },
];

export function UsersPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState<UserItem[]>(MOCK_USERS);

  const filtered = users.filter(
    (u) =>
      !search ||
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  const toggleActive = (id: string) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, is_active: !u.is_active } : u))
    );
  };

  const formatDate = (iso: string | null) =>
    iso
      ? new Date(iso).toLocaleDateString("fr-DZ", { day: "2-digit", month: "short", year: "numeric" })
      : t("common.never");

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── En-tête ─────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t("users.title")}</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {filtered.length} {t("common.totalItems", { count: filtered.length })}
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg
          text-sm hover:bg-brand-light transition-colors">
          <Plus className="w-4 h-4" />
          {t("users.add")}
        </button>
      </div>

      {/* ── Stats rapides ────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Object.entries(ROLE_CONFIG).map(([role, cfg]) => {
          const count = users.filter((u) => u.role === role).length;
          return (
            <div key={role} className="card p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{count}</p>
              <p className={`text-xs font-medium mt-1 px-2 py-0.5 rounded-full inline-block ${cfg.classes}`}>
                {t(cfg.labelKey)}
              </p>
            </div>
          );
        })}
      </div>

      {/* ── Recherche ────────────────────────────── */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder={t("users.searchPlaceholder") || "Rechercher un utilisateur..."}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg
            focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* ── Tableau ──────────────────────────────── */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-semibold text-gray-700">{t("users.fullName")}</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700">{t("users.role")}</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700 hidden md:table-cell">{t("users.lastLogin")}</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700 hidden lg:table-cell">{t("common.createdAt")}</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-700">{t("users.status")}</th>
                <th className="text-right px-4 py-3 font-semibold text-gray-700">{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((u) => {
                const roleCfg = ROLE_CONFIG[u.role];
                return (
                  <tr key={u.id} className={`hover:bg-gray-50 transition-colors ${!u.is_active ? "opacity-60" : ""}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-8 h-8 rounded-full flex items-center
                          justify-center text-white text-xs font-bold shrink-0
                          ${u.is_active ? "bg-brand" : "bg-gray-400"}`}>
                          {u.full_name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{u.full_name}</p>
                          <p className="text-xs text-gray-500">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${roleCfg?.classes}`}>
                        {roleCfg?.label || u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 hidden md:table-cell">
                      {formatDate(u.last_login)}
                    </td>
                    <td className="px-4 py-3 text-gray-500 hidden lg:table-cell">
                      {formatDate(u.date_joined)}
                    </td>
                    <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full
                      ${u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {u.is_active ? t("users.active") : t("users.inactive")}
                    </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
                          title={t("common.edit")}>
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => toggleActive(u.id)}
                          className={`p-1.5 rounded-lg transition-colors
                            ${u.is_active
                              ? "text-red-400 hover:bg-red-50 hover:text-red-600"
                              : "text-green-500 hover:bg-green-50 hover:text-green-700"}`}
                          title={u.is_active ? t("users.deactivate") : t("users.activate")}
                        >
                          {u.is_active
                            ? <UserX className="w-3.5 h-3.5" />
                            : <UserCheck className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
