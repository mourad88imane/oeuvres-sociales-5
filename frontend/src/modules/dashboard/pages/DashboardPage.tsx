/**
 * DASHBOARD PAGE — Tableau de bord principal de la plateforme
 * Données en temps réel depuis l'endpoint d'analytics.
 */
import {
  Users, Gift, Wallet, Clock,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Legend,
} from "recharts";
import { useAuthStore } from "@modules/auth/store/authStore";
import { useGlobalDashboard } from "@modules/analytics/api/index";
import { Spinner } from "@shared/components/ui/index";
import { fmtNumber, fmtDZD } from "@modules/analytics/utils/formatters";
import { RecommendationsWidget } from "@modules/ai/components/RecommendationsWidget";
import { AnomalyFeedWidget } from "@modules/ai/components/AnomalyFeedWidget";

const MONTH_LABELS: Record<string, string> = {
  "01": "Jan", "02": "Fév", "03": "Mar", "04": "Avr",
  "05": "Mai", "06": "Jun", "07": "Jul", "08": "Aoû",
  "09": "Sep", "10": "Oct", "11": "Nov", "12": "Déc",
};

export function DashboardPage() {
  const { user } = useAuthStore();
  const { data, isLoading } = useGlobalDashboard({ months: 6 });

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;

  const s = data?.summary;
  const trends = (data?.trends || []).map(t => ({
    ...t,
    monthLabel: MONTH_LABELS[t.month?.slice(5, 7) || ""] || t.month?.slice(0, 7) || t.month,
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── En-tête ─────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Bonjour, {user?.full_name?.split(" ")[0]}
        </h1>
        <p className="text-gray-500 mt-1 text-sm">
          Voici un aperçu de l'activité de la plateforme.
        </p>
      </div>

      {/* ── KPI Cards ───────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          title="Employés actifs"
          value={fmtNumber(s?.employees?.active ?? 0)}
          icon={Users}
          iconBg="bg-blue-100"
          iconColor="text-blue-600"
          trend={`${fmtNumber(s?.employees?.total ?? 0)} total`}
          trendPositive
        />
        <KpiCard
          title="Prestations totales"
          value={fmtNumber(s?.benefits?.total ?? 0)}
          icon={Gift}
          iconBg="bg-purple-100"
          iconColor="text-purple-600"
          trend={`${fmtNumber(s?.benefits?.pending ?? 0)} en attente`}
          trendPositive={false}
        />
        <KpiCard
          title="En attente de validation"
          value={fmtNumber(s?.benefits?.pending ?? 0)}
          icon={Clock}
          iconBg="bg-amber-100"
          iconColor="text-amber-600"
          trend="À traiter"
          trendPositive={false}
        />
        <KpiCard
          title="Montant total payé"
          value={fmtDZD(s?.finance?.total_paid ?? 0, true)}
          icon={Wallet}
          iconBg="bg-green-100"
          iconColor="text-green-600"
          trend={`${fmtDZD(s?.finance?.month_paid ?? 0, true)} ce mois`}
          trendPositive
        />
      </div>

      {/* ── Graphiques ──────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Évolution mensuelle */}
        <div className="card p-5 xl:col-span-2">
          <h2 className="text-base font-semibold text-gray-800 mb-4">
            Évolution mensuelle des prestations
          </h2>
          {trends.length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trends} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="monthLabel" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }}
                  formatter={(v: number) => fmtNumber(v)}
                />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Line
                  type="monotone" dataKey="benefits_count"
                  stroke="#3B82F6" strokeWidth={2}
                  dot={{ r: 3 }} name="Soumises"
                />
                <Line
                  type="monotone" dataKey="payments_count"
                  stroke="#22C55E" strokeWidth={2}
                  dot={{ r: 3 }} name="Payées"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Répartition par statut */}
        <div className="card p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-4">
            Répartition par statut
          </h2>
          {(s?.benefits?.by_type || []).length === 0 ? (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Aucune donnée</div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={(s?.benefits?.by_type || []).slice(0, 5)} layout="vertical" margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="benefit_type__name" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip
                    contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "12px" }}
                    formatter={(value) => [value, "Prestations"]}
                  />
                  <Bar dataKey="count" fill="#3B82F6" radius={[0, 4, 4, 0]} name="Count" />
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 space-y-2">
                {(s?.benefits?.by_type || []).slice(0, 5).map(({ benefit_type__name, count }, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500" />
                      <span className="text-xs text-gray-600 truncate max-w-[120px]">{benefit_type__name}</span>
                    </div>
                    <span className="text-xs font-semibold text-gray-800">{count}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Activités récentes ───────────────────────── */}
      <div className="card p-5">
        <h2 className="text-base font-semibold text-gray-800 mb-4">
          Aperçu rapide
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center py-4 bg-blue-50 rounded-xl">
            <p className="text-2xl font-bold text-blue-700">{fmtNumber(s?.employees?.active ?? 0)}</p>
            <p className="text-xs text-blue-500 mt-0.5">Employés actifs</p>
          </div>
          <div className="text-center py-4 bg-green-50 rounded-xl">
            <p className="text-2xl font-bold text-green-700">{fmtNumber(s?.beneficiaries?.active ?? 0)}</p>
            <p className="text-xs text-green-500 mt-0.5">Ayants droit</p>
          </div>
          <div className="text-center py-4 bg-amber-50 rounded-xl">
            <p className="text-2xl font-bold text-amber-700">{fmtNumber(s?.conventions?.active ?? 0)}</p>
            <p className="text-xs text-amber-500 mt-0.5">Conventions actives</p>
          </div>
          <div className="text-center py-4 bg-purple-50 rounded-xl">
            <p className="text-2xl font-bold text-purple-700">{fmtDZD(s?.finance?.total_paid ?? 0, true)}</p>
            <p className="text-xs text-purple-500 mt-0.5">Total payé</p>
          </div>
        </div>
      </div>

      {/* ── IA Widgets ───────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <RecommendationsWidget />
        <AnomalyFeedWidget />
      </div>
    </div>
  );
}

// ── Composant KPI Card ────────────────────────────────────
interface KpiCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  trend?: string;
  trendPositive?: boolean;
}

function KpiCard({ title, value, icon: Icon, iconBg, iconColor, trend, trendPositive }: KpiCardProps) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2.5 rounded-xl ${iconBg}`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        {trend && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full
            ${trendPositive ? "text-green-700 bg-green-50" : "text-amber-700 bg-amber-50"}`}>
            {trend}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
      <p className="text-sm text-gray-500">{title}</p>
    </div>
  );
}
