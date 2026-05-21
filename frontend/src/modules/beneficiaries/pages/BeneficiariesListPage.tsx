import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Users, Search, RefreshCw, UserCheck, UserX, GraduationCap,
  Heart, ChevronLeft, ChevronRight,
} from "lucide-react";
import { clsx } from "clsx";
import { useBeneficiaries } from "../api/index";
import { Badge, Spinner, EmptyState } from "@shared/components/ui/index";
import { fmtNumber } from "@modules/analytics/utils/formatters";

const RELATIONSHIPS = [
  { value: "", label: "Tous" },
  { value: "spouse", label: "Conjoint(e)" },
  { value: "child", label: "Enfant" },
  { value: "parent", label: "Parent" },
  { value: "sibling", label: "Frère/Sœur" },
  { value: "other", label: "Autre" },
];

const PAGE_SIZES = [10, 25, 50, 100];

export function BeneficiariesListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 25,
    search: "",
    relationship: "",
    eligible: "",
  });

  const { data, isLoading, isFetching, refetch } = useBeneficiaries(filters);
  const beneficiaries = data?.data ?? [];
  const count = data?.count ?? 0;

  const updateFilter = useCallback((key: string, value: unknown) => {
    setFilters(prev => ({ ...prev, [key]: value, page: key !== "page" ? 1 : (value as number) }));
  }, []);

  const totalPages = Math.max(1, Math.ceil(count / filters.page_size));

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ayants droit</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {isLoading ? "Chargement..." : `${fmtNumber(count)} ayant${count > 1 ? "s" : ""} droit`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => refetch()}
            className="p-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
            <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text" placeholder="Rechercher (nom, matricule, NNI…)"
            value={filters.search}
            onChange={e => updateFilter("search", e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select value={filters.relationship} onChange={e => updateFilter("relationship", e.target.value)}
          className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
          {RELATIONSHIPS.map(r => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>
        <select value={filters.eligible} onChange={e => updateFilter("eligible", e.target.value)}
          className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">Éligibilité: Tous</option>
          <option value="true">Éligible</option>
          <option value="false">Non éligible</option>
        </select>
        <select value={filters.page_size} onChange={e => updateFilter("page_size", Number(e.target.value))}
          className="text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
          {PAGE_SIZES.map(s => (
            <option key={s} value={s}>{s} / page</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-24"><Spinner size="lg" /></div>
      ) : beneficiaries.length === 0 ? (
        <EmptyState icon={Users} title="Aucun ayant droit"
          description={filters.search || filters.relationship || filters.eligible
            ? "Aucun résultat pour ces filtres." : "Aucun ayant droit enregistré."}
        />
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Nom & Prénom</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Employé</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Lien</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Âge</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">NNI</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Éligible</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Étudiant</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wider">Handicap</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {beneficiaries.map(b => (
                  <tr key={b.id} className="hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/employees/${b.employee}`)}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{b.full_name}</div>
                      <div className="text-xs text-gray-400">{b.gender_display}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-800">{b.employee_name}</div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={b.relationship === "spouse" ? "info" : b.relationship === "child" ? "success" : "default"}>
                        {b.relationship_display}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-gray-700">{b.age ?? "—"}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 font-mono">
                      {b.national_id || "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {b.is_eligible
                        ? <UserCheck className="w-4 h-4 text-green-500 mx-auto" />
                        : <UserX className="w-4 h-4 text-red-400 mx-auto" aria-label={b.ineligibility_reason} />
                      }
                    </td>
                    <td className="px-4 py-3 text-center">
                      {b.is_student
                        ? <GraduationCap className="w-4 h-4 text-blue-500 mx-auto" />
                        : <span className="text-gray-300">—</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-center">
                      {b.is_handicapped
                        ? <Heart className="w-4 h-4 text-amber-500 mx-auto" />
                        : <span className="text-gray-300">—</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
            <span className="text-xs text-gray-500">
              Page {filters.page} sur {totalPages} · {fmtNumber(count)} total
            </span>
            <div className="flex items-center gap-1">
              <button onClick={() => updateFilter("page", filters.page - 1)} disabled={filters.page <= 1}
                className="p-1.5 rounded border border-gray-300 text-gray-600 hover:bg-white disabled:opacity-30 disabled:cursor-default">
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                const p = i + 1;
                return (
                  <button key={p} onClick={() => updateFilter("page", p)}
                    className={clsx("px-3 py-1 rounded text-xs font-medium",
                      p === filters.page ? "bg-brand text-white" : "text-gray-600 hover:bg-white border border-gray-300"
                    )}>{p}</button>
                );
              })}
              <button onClick={() => updateFilter("page", filters.page + 1)} disabled={filters.page >= totalPages}
                className="p-1.5 rounded border border-gray-300 text-gray-600 hover:bg-white disabled:opacity-30 disabled:cursor-default">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
