import { useState } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area,
} from "recharts";
import {
  Users, UserCheck, Gift, Wallet, Building2,
  RefreshCw, BarChart3,
} from "lucide-react";
import { clsx } from "clsx";
import { useGlobalAnalytics, useKpiHistory, useSnapshotKpis } from "../api/index";
import {
  AnalyticsKpiCard, AnalyticsStatCard, CategorySummaryCard,
  ChartTooltip,
} from "../components/AnalyticsComponents";
import { Spinner } from "@shared/components/ui/index";
import { fmtDZD, fmtPct, fmtNumber, fmtDate, CHART_COLORS, CATEGORY_LABELS } from "../utils/formatters";
import type { MonthlyTrend } from "../types";

export function AnalyticsDashboardPage() {
  const [period, setPeriod] = useState<string>("12m");
  const months = period === "6m" ? 6 : period === "3m" ? 3 : period === "1m" ? 1 : 12;
  const [selectedKpi, setSelectedKpi] = useState<string>("consumption_rate");

  const { data: globalData, isLoading, refetch } = useGlobalAnalytics({ months });
  const { data: kpiHistory } = useKpiHistory(selectedKpi, 90);
  const snapshotMut = useSnapshotKpis();

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;
  if (!globalData) return (
    <div className="text-center py-16 text-gray-400">
      <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>Aucune donnée analytique disponible</p>
    </div>
  );

  const { summary, trends, top, kpis: globalKpis } = globalData;
  const s = summary;
  const monthlyData = (trends || []).map(m => ({
    ...m,
    monthLabel: m.month?.slice(0, 7) || m.month,
  }));

  const benefitsByType = (top?.top_benefit_types || []).map(t => ({
    name: t.benefit_type__name || t.benefit_type__code || "N/A",
    value: t.total,
    count: t.count,
  }));

  const deptBenefits = (top?.top_departments_by_benefits || []).map(d => ({
    name: d.employee__department__name || "N/A",
    montant: d.total,
    count: d.count,
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 text-sm">Tableau de bord analytique · {fmtDate(globalData.date)}</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={period} onChange={e => setPeriod(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option value="12m">12 mois</option>
            <option value="6m">6 mois</option>
            <option value="3m">3 mois</option>
            <option value="1m">1 mois</option>
          </select>
          <button onClick={() => snapshotMut.mutate()} disabled={snapshotMut.isPending}
            className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${snapshotMut.isPending ? "animate-spin" : ""}`} />
            Snapshot KPI
          </button>
          <button onClick={() => refetch()}
            className="p-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Row 1: KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-5 gap-3">
        <AnalyticsStatCard
          label="Employés" value={fmtNumber(s.employees?.total ?? 0)}
          sub={`${fmtNumber(s.employees?.active ?? 0)} actifs`}
          icon={Users} iconBg="bg-blue-100" iconColor="text-blue-600"
        />
        <AnalyticsStatCard
          label="Ayants droit" value={fmtNumber(s.beneficiaries?.total ?? 0)}
          sub={`${fmtNumber(s.beneficiaries?.active ?? 0)} actifs`}
          icon={UserCheck} iconBg="bg-green-100" iconColor="text-green-600"
        />
        <AnalyticsStatCard
          label="Prestations" value={fmtNumber(s.benefits?.total ?? 0)}
          sub={`${fmtDZD(s.benefits?.total_amount ?? 0, true)} total`}
          icon={Gift} iconBg="bg-amber-100" iconColor="text-amber-600"
        />
        <AnalyticsStatCard
          label="Conventions" value={fmtNumber(s.conventions?.active ?? 0)}
          sub={`${fmtNumber(s.conventions?.total ?? 0)} total`}
          icon={Building2} iconBg="bg-purple-100" iconColor="text-purple-600"
        />
        <AnalyticsStatCard
          label="Budget" value={fmtDZD(s.finance?.total_budget ?? 0, true)}
          sub={`${fmtDZD(s.finance?.total_paid ?? 0, true)} payé`}
          icon={Wallet} iconBg="bg-emerald-100" iconColor="text-emerald-600"
          alert={(s.finance?.pending_payments ?? 0) > 20}
        />
      </div>

      {/* Row 2: Category summaries */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <CategorySummaryCard title="Employés" icon={Users} color="#1A3C6E" stats={[
          { label: "Total", value: fmtNumber(s.employees?.total ?? 0) },
          { label: "Actifs", value: fmtNumber(s.employees?.active ?? 0) },
          { label: "Nouveaux ce mois", value: fmtNumber(s.employees?.new_this_month ?? 0) },
          { label: "Taux d'activité", value: fmtPct(s.employees?.total ? (s.employees.active / s.employees.total) * 100 : 0) },
        ]} />
        <CategorySummaryCard title="Prestations" icon={Gift} color="#F59E0B" stats={[
          { label: "Total", value: fmtNumber(s.benefits?.total ?? 0) },
          { label: "En attente", value: fmtNumber(s.benefits?.pending ?? 0), alert: (s.benefits?.pending ?? 0) > 10 },
          { label: "Approuvées", value: fmtNumber(s.benefits?.approved ?? 0) },
          { label: "Montant mois", value: fmtDZD(s.benefits?.month_amount ?? 0, true) },
        ]} />
        <CategorySummaryCard title="Conventions" icon={Building2} color="#8B5CF6" stats={[
          { label: "Total", value: fmtNumber(s.conventions?.total ?? 0) },
          { label: "Actives", value: fmtNumber(s.conventions?.active ?? 0) },
          { label: "Expiration proche", value: fmtNumber(s.conventions?.expiring_soon ?? 0), alert: (s.conventions?.expiring_soon ?? 0) > 0 },
          { label: "Expirées", value: fmtNumber(s.conventions?.expired ?? 0), alert: (s.conventions?.expired ?? 0) > 0 },
        ]} />
        <CategorySummaryCard title="Finance" icon={Wallet} color="#10B981" stats={[
          { label: "Budget total", value: fmtDZD(s.finance?.total_budget ?? 0, true) },
          { label: "Total payé", value: fmtDZD(s.finance?.total_paid ?? 0, true) },
          { label: "Payé ce mois", value: fmtDZD(s.finance?.month_paid ?? 0, true) },
          { label: "Paiements en attente", value: fmtNumber(s.finance?.pending_payments ?? 0), alert: (s.finance?.pending_payments ?? 0) > 20 },
        ]} />
      </div>

      {/* Row 3: Main chart + KPIs */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Tendance des paiements */}
        <div className="card p-5 xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Tendance mensuelle</h3>
            <div className="flex gap-3 text-xs text-gray-500">
              <span className="flex items-center gap-1"><div className="w-2.5 h-2.5 rounded bg-[#10B981]" /> Paiements</span>
              <span className="flex items-center gap-1"><div className="w-2.5 h-2.5 rounded bg-[#1A3C6E]" /> Prestations</span>
            </div>
          </div>
          {monthlyData.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={monthlyData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <defs>
                  <linearGradient id="paymentsGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.2} /><stop offset="95%" stopColor="#10B981" stopOpacity={0} /></linearGradient>
                  <linearGradient id="benefitsGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#1A3C6E" stopOpacity={0.2} /><stop offset="95%" stopColor="#1A3C6E" stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000000).toFixed(1)}M`} />
                <Tooltip content={<ChartTooltip formatter={(v) => fmtDZD(v)} />} />
                <Area yAxisId="left" type="monotone" dataKey="payments_amount" stroke="#10B981" fill="url(#paymentsGrad)" strokeWidth={2} name="Paiements" />
                <Area yAxisId="left" type="monotone" dataKey="benefits_amount" stroke="#1A3C6E" fill="url(#benefitsGrad)" strokeWidth={2} name="Prestations" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* KPI Cards grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-700 px-1">Indicateurs clés</h3>
          <div className="grid grid-cols-1 gap-3">
            {(globalKpis || []).slice(0, 6).map(kpi => (
              <AnalyticsKpiCard key={kpi.id} kpi={kpi} onClick={() => setSelectedKpi(kpi.code)} />
            ))}
          </div>
        </div>
      </div>

      {/* Row 4: Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Répartition par type de prestation */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Répartition par type de prestation</h3>
          {benefitsByType.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie data={benefitsByType} cx="50%" cy="50%" innerRadius={45} outerRadius={85}
                    dataKey="value" nameKey="name" paddingAngle={2}>
                    {benefitsByType.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val: number) => fmtDZD(val)} contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-2">
                {benefitsByType.slice(0, 6).map((t, i) => (
                  <div key={t.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                      <span className="text-gray-600 truncate max-w-[100px]">{t.name}</span>
                    </div>
                    <span className="font-medium text-gray-800">{fmtDZD(t.value, true)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Top départements */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Top départements par montant</h3>
          {deptBenefits.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={deptBenefits.slice(0, 8)} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000000).toFixed(1)}M`} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
                <Tooltip formatter={(val: number) => fmtDZD(val)} contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                <Bar dataKey="montant" fill="#1A3C6E" radius={[0, 4, 4, 0]} name="Montant">
                  {deptBenefits.slice(0, 8).map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Row 5: KPI History + Top partners */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* KPI History Chart */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700">
              Historique KPI : <span className="text-brand">{(globalKpis || []).find(k => k.code === selectedKpi)?.name || selectedKpi}</span>
            </h3>
            <select value={selectedKpi} onChange={e => setSelectedKpi(e.target.value)}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none">
              {(globalKpis || []).slice(0, 20).map(k => (
                <option key={k.code} value={k.code}>{k.name}</option>
              ))}
            </select>
          </div>
          {!kpiHistory || kpiHistory.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              Aucun historique. Utilisez "Snapshot KPI" pour générer des données.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={kpiHistory.map(h => ({ ...h, dateLabel: h.date?.slice(5, 10) || "" }))} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="dateLabel" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                <Line type="monotone" dataKey="value" stroke="#1A3C6E" strokeWidth={2} dot={{ r: 3 }} name="Valeur" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Partners */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Top partenaires (conventions)</h3>
          {!top?.top_partners || top.top_partners.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <div className="space-y-3">
              {top.top_partners.slice(0, 8).map((p, i) => (
                <div key={p.partner__code || i} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 font-mono w-6">{String(i + 1).padStart(2, "0")}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between text-sm mb-0.5">
                      <span className="font-medium text-gray-800 truncate max-w-[160px]">{p.partner__name}</span>
                      <span className="text-xs font-semibold text-gray-600">{fmtDZD(p.total, true)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span className="font-mono">{p.partner__code}</span>
                      <span>· {p.count} convention(s)</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Top employees */}
      {top?.top_employees_by_amount && top.top_employees_by_amount.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Top employés par montant de prestations</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-3 py-2 font-semibold text-gray-600">#</th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-600">Employé</th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-600">Matricule</th>
                  <th className="text-right px-3 py-2 font-semibold text-gray-600">Prestations</th>
                  <th className="text-right px-3 py-2 font-semibold text-gray-600">Montant total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {top.top_employees_by_amount.slice(0, 10).map((e, i) => (
                  <tr key={e.employee__matricule || i} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-xs text-gray-400">{i + 1}</td>
                    <td className="px-3 py-2 font-medium text-gray-800">{e.employee__full_name}</td>
                    <td className="px-3 py-2 text-xs text-gray-500 font-mono">{e.employee__matricule}</td>
                    <td className="px-3 py-2 text-right text-gray-600">{e.count}</td>
                    <td className="px-3 py-2 text-right font-medium">{fmtDZD(e.total, true)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
