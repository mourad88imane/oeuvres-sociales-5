/**
 * FINANCE DASHBOARD — Tableau de bord financier complet
 */
import { useState } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Wallet, TrendingUp, AlertTriangle, CheckCircle2,
  Clock, Download, RefreshCw,
} from "lucide-react";
import { useFinanceDashboard, useFiscalYears, useAlerts, useExportPayments } from "../api/index";
import { AlertPanel, FinanceKpiCard, ConsumptionBar } from "../components/FinanceComponents";
import { Spinner } from "@shared/components/ui/index";
import { fmtDZD, fmtPct, CHART_COLORS } from "../utils/formatters";

export function FinanceDashboardPage() {
  const [selectedFY, setSelectedFY] = useState<string>("");

  const { data: fyList }   = useFiscalYears();
  const { data: dashboard, isLoading, refetch } = useFinanceDashboard(selectedFY || undefined);
  const { data: alertData }= useAlerts({ unresolved: "true", page_size: "10" });
  const exportMut           = useExportPayments();

  const fiscalYears = fyList?.results ?? [];
  const alerts      = alertData?.results ?? [];

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;
  if (!dashboard?.fiscal_year) return (
    <div className="text-center py-16 text-gray-400">
      <Wallet className="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>Aucun exercice fiscal actif. Créez et ouvrez un exercice fiscal pour commencer.</p>
    </div>
  );

  const fy = dashboard.fiscal_year!;
  const py = dashboard.payments!;
  const bu = dashboard.budgets!;

  // Données graphiques
  const byStatusData = py.by_status.map(s => ({
    name:   s.status, label: s.status,
    count:  s.count,
    amount: s.total,
  }));

  const monthlyData = dashboard.monthly_trend.map(m => ({
    month:  m.month,
    count:  m.count,
    amount: m.amount / 1000, // En milliers pour lisibilité
  }));

  const budgetPieData = [
    { name: "Payé",     value: bu.total_paid,                                  color: "#10B981" },
    { name: "Disponible", value: bu.total_allocated - bu.total_paid, color: "#E5E7EB" },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── En-tête ─────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Finance</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {fy.label} · Exercice {fy.status === "open" ? "ouvert" : fy.status}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Sélecteur exercice */}
          <select value={selectedFY} onChange={e => setSelectedFY(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option value="">Exercice actif</option>
            {fiscalYears.map(f => (
              <option key={f.id} value={f.id}>{f.year} — {f.label}</option>
            ))}
          </select>
          <button onClick={() => refetch()}
            className="p-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => exportMut.mutate({ fiscal_year: fy.id })}
            disabled={exportMut.isPending}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50">
            <Download className="w-4 h-4" />Export
          </button>
        </div>
      </div>

      {/* ── Barre de consommation globale ───────────── */}
      <div className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">
              Budget {fy.year} — Consommation globale
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {fmtDZD(fy.total_paid)} payés sur {fmtDZD(fy.total_budget)} alloués
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-brand">{fmtPct(fy.consumption_rate)}</p>
            <p className="text-xs text-gray-400">Disponible : {fmtDZD(fy.available)}</p>
          </div>
        </div>
        <ConsumptionBar rate={Number(fy.consumption_rate)} height="h-4" />
      </div>

      {/* ── KPI Cards ───────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <FinanceKpiCard
          label="Total payé"
          value={fmtDZD(py.total_paid, true)}
          sub={`${py.paid_count} paiements`}
          icon={CheckCircle2}
          iconBg="bg-green-100" iconColor="text-green-600"
        />
        <FinanceKpiCard
          label="En attente de paiement"
          value={String(py.pending_count)}
          sub="paiements à traiter"
          icon={Clock}
          iconBg="bg-amber-100" iconColor="text-amber-600"
          alert={py.pending_count > 20}
        />
        <FinanceKpiCard
          label="Budgets en alerte"
          value={String(bu.alert_count)}
          sub={`${bu.overrun_count} dépassement(s)`}
          icon={AlertTriangle}
          iconBg="bg-red-100" iconColor="text-red-600"
          alert={bu.overrun_count > 0}
        />
        <FinanceKpiCard
          label="Anomalies IA détectées"
          value={String(py.anomaly_count)}
          sub="À vérifier"
          icon={TrendingUp}
          iconBg="bg-purple-100" iconColor="text-purple-600"
          alert={py.anomaly_count > 0}
        />
      </div>

      {/* ── Graphiques ──────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Tendance mensuelle */}
        <div className="card p-5 xl:col-span-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Évolution mensuelle des paiements
          </h3>
          {monthlyData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              Aucune donnée mensuelle disponible
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={monthlyData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left"  tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: number, name: string) =>
                    name === "amount" ? [`${(val * 1000).toLocaleString("fr-DZ")} DZD`, "Montant"] : [val, "Paiements"]
                  }
                  contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }}
                />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Line yAxisId="left"  type="monotone" dataKey="count"  stroke="#1A3C6E" strokeWidth={2} dot={{ r: 3 }} name="Paiements" />
                <Line yAxisId="right" type="monotone" dataKey="amount" stroke="#10B981" strokeWidth={2} dot={{ r: 3 }} name="Montant (K DZD)" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Répartition budget */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Répartition du budget</h3>
          {budgetPieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={budgetPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                    dataKey="value" nameKey="name" paddingAngle={2}>
                    {budgetPieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: number) => fmtDZD(val)}
                    contentStyle={{ borderRadius: "8px", fontSize: "12px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {budgetPieData.map(d => (
                  <div key={d.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full shrink-0" style={{ background: d.color }} />
                      <span className="text-gray-600">{d.name}</span>
                    </div>
                    <span className="font-medium text-gray-800">{fmtDZD(d.value, true)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              Aucune donnée budgétaire
            </div>
          )}
        </div>
      </div>

      {/* ── Top types + Alertes ─────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Top types de prestation */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Top dépenses par prestation</h3>
          {dashboard.top_benefit_types.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={dashboard.top_benefit_types.map(t => ({
                  name:   t.code,
                  full:   t.name,
                  count:  t.count,
                  amount: t.total / 1000,
                }))}
                layout="vertical"
                margin={{ left: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={60} />
                <Tooltip
                  formatter={(val: number, name: string) =>
                    name === "amount" ? [`${(val * 1000).toLocaleString("fr-DZ")} DZD`, "Montant"] : [val, "Nb"]
                  }
                  contentStyle={{ borderRadius: "8px", fontSize: "12px" }}
                />
                <Bar dataKey="amount" fill="#1A3C6E" radius={[0, 4, 4, 0]} name="Montant (K DZD)">
                  {dashboard.top_benefit_types.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Alertes */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">
              Alertes financières
              {alerts.length > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                  {alerts.length}
                </span>
              )}
            </h3>
          </div>
          <AlertPanel alerts={alerts} maxItems={6} />
        </div>
      </div>

      {/* ── Répartition par statut paiement ─────────── */}
      {byStatusData.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Paiements par statut
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-3">
            {byStatusData.map((s) => {
              const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
                pending:    { label: "En attente",    cls: "bg-amber-100 text-amber-700"   },
                approved:   { label: "Approuvé",      cls: "bg-blue-100 text-blue-700"     },
                processing: { label: "En traitement", cls: "bg-purple-100 text-purple-700" },
                paid:       { label: "Payé",          cls: "bg-green-100 text-green-700"   },
                failed:     { label: "Échoué",        cls: "bg-red-100 text-red-700"       },
                cancelled:  { label: "Annulé",        cls: "bg-gray-100 text-gray-500"     },
                reversed:   { label: "Inversé",       cls: "bg-orange-100 text-orange-700" },
              };
              const cfg = STATUS_LABELS[s.name] ?? { label: s.name, cls: "bg-gray-100 text-gray-600" };
              return (
                <div key={s.name} className={`rounded-xl p-3 text-center ${cfg.cls}`}>
                  <p className="text-xl font-bold">{s.count}</p>
                  <p className="text-xs font-medium mt-0.5">{cfg.label}</p>
                  {s.amount > 0 && (
                    <p className="text-xs opacity-75 mt-1">{fmtDZD(s.amount, true)}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
