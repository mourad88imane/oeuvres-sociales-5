/**
 * PAYMENTS PAGE — Liste des paiements avec actions
 */
import { useState, useCallback } from "react";
import { Wallet, Search, Download, RefreshCw, SlidersHorizontal, ChevronLeft, ChevronRight } from "lucide-react";
import { usePayments, useExportPayments, useActiveFiscalYear } from "../api/index";
import { PaymentStatusBadge, PaymentActions } from "../components/FinanceComponents";
import { EmptyState, Spinner, Modal } from "@shared/components/ui/index";
import { RoleGuard } from "@shared/components/layout/ProtectedRoute";
import { fmtDZD, fmtDate } from "../utils/formatters";
import type { PaymentFilters, Payment } from "../types";

export function PaymentsPage() {
  const [filters,   setFilters]   = useState<PaymentFilters>({ page: 1, page_size: 25, ordering: "-created_at" });
  const [showFilters, setShowFilters] = useState(false);
  const [selected,  setSelected]  = useState<Payment | null>(null);

  const { data, isLoading, refetch, isFetching } = usePayments(filters);
  useActiveFiscalYear();
  const exportMut = useExportPayments();

  const payments   = data?.results   ?? [];
  const pagination = data?.pagination;

  const upd = useCallback((key: keyof PaymentFilters, val: unknown) => {
    setFilters(p => ({ ...p, [key]: val, page: key !== "page" ? 1 : val as number }));
  }, []);

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Paiements</h1>
          <p className="text-gray-500 text-sm">{pagination?.count ?? "—"} paiement{(pagination?.count ?? 0) > 1 ? "s" : ""}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => refetch()} className="p-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
            <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
          </button>
          <RoleGuard roles={["admin","comptable"]}>
            <button onClick={() => exportMut.mutate(filters)} disabled={exportMut.isPending}
              className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50">
              <Download className="w-4 h-4" />Export Excel
            </button>
          </RoleGuard>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 space-y-3">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Référence, employé, matricule..."
              value={filters.search ?? ""} onChange={e => upd("search", e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <button onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-2 border rounded-lg text-sm ${showFilters ? "border-brand bg-blue-50 text-brand" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}>
            <SlidersHorizontal className="w-4 h-4" />Filtres
          </button>
        </div>
        {showFilters && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3 border-t border-gray-100">
            {[
              { key:"status", label:"Statut", opts:[["","Tous"],["pending","En attente"],["approved","Approuvé"],["paid","Payé"],["cancelled","Annulé"]] },
              { key:"ordering", label:"Tri", opts:[["-created_at","Plus récent"],["-amount","Montant ↓"],["amount","Montant ↑"]] },
            ].map(({ key, label, opts }) => (
              <div key={key}>
                <label className="text-xs text-gray-500 mb-1 block">{label}</label>
                <select value={(filters as Record<string, unknown>)[key] as string ?? ""}
                  onChange={e => upd(key as keyof PaymentFilters, e.target.value)}
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none">
                  {opts.map(([v,l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
            ))}
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Anomalies IA</label>
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer mt-2">
                <input type="checkbox" checked={!!filters.anomaly_only}
                  onChange={e => upd("anomaly_only", e.target.checked)}
                  className="w-4 h-4 rounded accent-brand" />
                Anomalies uniquement
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : payments.length === 0 ? (
          <EmptyState icon={Wallet} title="Aucun paiement" description="Aucun paiement ne correspond à vos critères." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  {["Référence","Employé","Prestation","Montant","Statut","Mode","Date","Actions"].map((h, i) => (
                    <th key={h} className={`text-left px-4 py-3 font-semibold text-gray-700 ${i > 3 && i < 6 ? "hidden md:table-cell" : ""} ${i === 6 ? "hidden lg:table-cell" : ""}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {payments.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-mono text-xs text-gray-800">{p.reference}</p>
                        {p.anomaly_flag && <span className="text-xs text-amber-600">⚠ Anomalie</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{p.employee_name}</p>
                      <p className="text-xs text-gray-500">{p.employee_matricule}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-gray-700">{p.benefit_type_name}</p>
                      <p className="text-xs text-gray-400 font-mono">{p.benefit_ref}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-bold text-gray-900">{fmtDZD(p.amount)}</p>
                      {p.fees > 0 && <p className="text-xs text-gray-400">Frais : {fmtDZD(p.fees)}</p>}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell"><PaymentStatusBadge status={p.status} /></td>
                    <td className="px-4 py-3 hidden md:table-cell text-xs text-gray-600">{p.method_display}</td>
                    <td className="px-4 py-3 hidden lg:table-cell text-xs text-gray-500">
                      {p.executed_date ? fmtDate(p.executed_date) : fmtDate(p.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button onClick={() => setSelected(p)}
                          className="text-xs text-brand hover:underline">Voir</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
            <p className="text-xs text-gray-500">{pagination.count} résultats</p>
            <div className="flex items-center gap-1">
              <button onClick={() => upd("page",(filters.page??1)-1)} disabled={!pagination.previous}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-100"><ChevronLeft className="w-4 h-4" /></button>
              <span className="px-3 py-1.5 text-sm text-brand font-medium">{pagination.page} / {pagination.total_pages}</span>
              <button onClick={() => upd("page",(filters.page??1)+1)} disabled={!pagination.next}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-100"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>

      {/* Payment detail modal */}
      <Modal open={!!selected} onClose={() => setSelected(null)} title={`Paiement — ${selected?.reference}`} size="md">
        {selected && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[
                ["Employé",    selected.employee_name],
                ["Matricule",  selected.employee_matricule],
                ["Prestation", selected.benefit_type_name],
                ["Réf. presta",selected.benefit_ref],
                ["Montant",    fmtDZD(selected.amount)],
                ["Mode",       selected.method_display],
                ["Budget",     selected.budget_code || "—"],
                ["Exercice",   selected.fiscal_year_label],
                ["Réf. banque",selected.bank_reference || "—"],
                ["Date exec.", fmtDate(selected.executed_date)],
              ].map(([l,v]) => (
                <div key={l} className="bg-gray-50 rounded-lg px-3 py-2">
                  <p className="text-xs text-gray-400">{l}</p>
                  <p className="text-sm font-medium text-gray-800 truncate">{v}</p>
                </div>
              ))}
            </div>
            <PaymentStatusBadge status={selected.status} />
            <PaymentActions payment={selected} onUpdate={() => { refetch(); setSelected(null); }} />
          </div>
        )}
      </Modal>
    </div>
  );
}
