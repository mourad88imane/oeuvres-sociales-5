import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Building2, Search, RefreshCw, Plus, ChevronLeft, ChevronRight,
} from "lucide-react";
import { clsx } from "clsx";
import { usePartners } from "../api/index";
import { EmptyState, Spinner, Modal, Field, inputCls } from "@shared/components/ui/index";
import { RoleGuard } from "@shared/components/layout/ProtectedRoute";
import { PARTNER_TYPE_UI } from "../types";
import { useCreatePartner } from "../api/index";

export function PartnersPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, refetch } = usePartners({ search, type: typeFilter, page, page_size: 25 });
  const createMut = useCreatePartner();

  const partners = data?.results ?? [];
  const pagination = data?.pagination;

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const data: Record<string, unknown> = {};
    fd.forEach((v, k) => { data[k] = v; });
    await createMut.mutateAsync(data);
    setShowCreate(false);
    refetch();
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Partenaires</h1>
          <p className="text-gray-500 text-sm">{pagination?.count ?? "—"} partenaire(s)</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => refetch()}
            className="p-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
            <RefreshCw className="w-4 h-4" />
          </button>
          <RoleGuard roles={["admin","gestionnaire"]}>
            <button onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-3 py-2 bg-brand text-white text-sm rounded-lg hover:bg-blue-800">
              <Plus className="w-4 h-4" />Nouveau partenaire
            </button>
          </RoleGuard>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="card p-4 flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input type="text" placeholder="Code, nom, email, contact..."
            value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" />
        </div>
        <select value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(1); }}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none">
          <option value="">Tous les types</option>
          {Object.entries(PARTNER_TYPE_UI).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : partners.length === 0 ? (
          <EmptyState icon={Building2} title="Aucun partenaire"
            description="Créez votre premier partenaire." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  {["Code", "Nom", "Type", "Ville", "Wilaya", "Contact", "Email", "Actif", ""].map(h => (
                    <th key={h} className="text-left px-4 py-3 font-semibold text-gray-700">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {partners.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">{p.code}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{p.name}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">{p.type_display}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{p.city || "—"}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{p.wilaya || "—"}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{p.contact_name || "—"}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{p.email || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full",
                        p.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500")}>
                        {p.is_active ? "Oui" : "Non"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => navigate(`/conventions?partner_id=${p.id}`)}
                        className="text-xs text-brand hover:underline">
                        Voir conventions
                      </button>
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
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!pagination.previous}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-100">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-3 py-1.5 text-sm text-brand font-medium">
                {pagination.page} / {pagination.total_pages}
              </span>
              <button onClick={() => setPage(p => p + 1)} disabled={!pagination.next}
                className="p-1.5 rounded-lg border border-gray-200 disabled:opacity-40 hover:bg-gray-100">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)}
        title="Nouveau partenaire" size="lg"
        footer={
          <>
            <button onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Annuler</button>
            <button type="submit" form="create-partner-form" disabled={createMut.isPending}
              className="flex items-center gap-2 px-5 py-2 bg-brand text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-60">
              {createMut.isPending && <Spinner size="sm" />}Créer
            </button>
          </>
        }>
        <form id="create-partner-form" onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Code" required>
              <input name="code" className={inputCls()} required placeholder="EX: HOSP-001" />
            </Field>
            <Field label="Raison sociale" required>
              <input name="name" className={inputCls()} required placeholder="Nom du partenaire" />
            </Field>
          </div>
          <Field label="Type" required>
            <select name="type" className={inputCls()} required>
              {Object.entries(PARTNER_TYPE_UI).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Email">
              <input type="email" name="email" className={inputCls()} placeholder="contact@exemple.dz" />
            </Field>
            <Field label="Téléphone">
              <input name="phone" className={inputCls()} placeholder="+213 XX XXX XXX" />
            </Field>
          </div>
          <Field label="Adresse">
            <textarea name="address" rows={2} className={inputCls()} placeholder="Adresse complète..." />
          </Field>
          <div className="grid grid-cols-3 gap-4">
            <Field label="Ville">
              <input name="city" className={inputCls()} />
            </Field>
            <Field label="Wilaya">
              <input name="wilaya" className={inputCls()} />
            </Field>
            <Field label="Code postal">
              <input name="postal_code" className={inputCls()} />
            </Field>
          </div>
          <div className="border-t border-gray-200 pt-4">
            <p className="text-xs font-semibold text-gray-500 mb-3">Personne de contact</p>
            <div className="grid grid-cols-3 gap-4">
              <Field label="Nom">
                <input name="contact_name" className={inputCls()} />
              </Field>
              <Field label="Téléphone">
                <input name="contact_phone" className={inputCls()} />
              </Field>
              <Field label="Email">
                <input type="email" name="contact_email" className={inputCls()} />
              </Field>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}
