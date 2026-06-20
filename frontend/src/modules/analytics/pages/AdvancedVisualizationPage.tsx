import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BarChart3, TrendingUp, Download, Calendar, Filter, RefreshCw } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area,
} from "recharts";
import { useGlobalDashboard, useAnalyticsTrends } from "../api";

const COLORS = ["#ffda2d", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ef4444"];

export function AdvancedVisualizationPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState(12);
  const [chartType, setChartType] = useState<"bar" | "line" | "area" | "pie">("bar");
  const [metric, setMetric] = useState("benefits");

  const { data: dashboard, isLoading: dashboardLoading } = useGlobalDashboard();
  const { data: trends, isLoading: trendsLoading } = useAnalyticsTrends(period);

  const trendsData = trends?.map((d: Record<string, unknown>) => ({
    month: d.month_label || d.month || "",
    amount: Number(d.amount) || 0,
    count: Number(d.count) || 0,
    employees: Number(d.employees) || 0,
    payments: Number(d.payments) || 0,
  })) || [];

  const summary = dashboard?.summary || {};
  const pieData = [
    { name: t("analytics.benefits"), value: Number(summary.total_benefits) || 0 },
    { name: t("analytics.payments"), value: Number(summary.total_payments) || 0 },
    { name: t("conventions.title"), value: Number(summary.active_conventions) || 0 },
    { name: t("employees.title"), value: Number(summary.active_employees) || 0 },
  ].filter(d => d.value > 0);

  const metricKey = metric === "payments" ? "payments" : metric === "employees" ? "employees" : "amount";

  const handleExport = () => {
    const csv = [
      ["Mois", "Montant", "Nombre", "Employés", "Paiements"].join(","),
      ...trendsData.map(r =>
        [r.month, r.amount, r.count, r.employees, r.payments].join(",")
      ),
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report_${metric}_${period}m.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-brand/10">
            <BarChart3 className="w-6 h-6 text-brand" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t("analytics.title")}</h1>
            <p className="text-sm text-gray-500">{t("analytics.dashboard")}</p>
          </div>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand text-[#1a1917] font-bold text-sm hover:brightness-95"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={metric}
            onChange={e => setMetric(e.target.value)}
            className="text-sm rounded-xl border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="benefits">{t("analytics.benefits")}</option>
            <option value="payments">{t("analytics.payments")}</option>
            <option value="employees">{t("analytics.employees")}</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <select
            value={period}
            onChange={e => setPeriod(Number(e.target.value))}
            className="text-sm rounded-xl border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value={6}>6 {t("dashboard.months.06").toLowerCase()}</option>
            <option value={12}>12 {t("dashboard.months.12").toLowerCase()}</option>
            <option value={24}>24 {t("dashboard.months.01").toLowerCase()}</option>
          </select>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setChartType("bar")}
            className={`px-3 py-1.5 text-xs rounded-lg font-semibold ${chartType === "bar" ? "bg-brand text-[#1a1917]" : "text-gray-500 hover:bg-gray-100"}`}
          >
            Barres
          </button>
          <button
            onClick={() => setChartType("line")}
            className={`px-3 py-1.5 text-xs rounded-lg font-semibold ${chartType === "line" ? "bg-brand text-[#1a1917]" : "text-gray-500 hover:bg-gray-100"}`}
          >
            Lignes
          </button>
          <button
            onClick={() => setChartType("area")}
            className={`px-3 py-1.5 text-xs rounded-lg font-semibold ${chartType === "area" ? "bg-brand text-[#1a1917]" : "text-gray-500 hover:bg-gray-100"}`}
          >
            Aires
          </button>
          <button
            onClick={() => setChartType("pie")}
            className={`px-3 py-1.5 text-xs rounded-lg font-semibold ${chartType === "pie" ? "bg-brand text-[#1a1917]" : "text-gray-500 hover:bg-gray-100"}`}
          >
            Secteurs
          </button>
        </div>
      </div>

      {/* Main chart */}
      <div className="card">
        <h2 className="font-bold text-gray-800 mb-4 capitalize">{metric} — {period} mois</h2>
        {trendsLoading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="w-6 h-6 animate-spin text-gray-300" />
          </div>
        ) : trendsData.length === 0 ? (
          <div className="text-center py-20 text-gray-400 text-sm">{t("analytics.noData")}</div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            {chartType === "bar" ? (
              <BarChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey={metricKey} fill="#ffda2d" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : chartType === "line" ? (
              <LineChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey={metricKey} stroke="#ffda2d" strokeWidth={2} dot={{ fill: "#ffda2d" }} />
              </LineChart>
            ) : chartType === "area" ? (
              <AreaChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey={metricKey} stroke="#ffda2d" fill="#ffda2d" fillOpacity={0.2} />
              </AreaChart>
            ) : (
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={140} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            )}
          </ResponsiveContainer>
        )}
      </div>

      {/* KPI Cards */}
      {dashboard && !dashboardLoading && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: t("dashboard.totalBenefits"), value: summary.total_benefits ?? "—", color: "bg-amber-50 text-amber-700" },
            { label: t("finance.totalSpent"), value: summary.total_paid ? `${(Number(summary.total_paid) / 1000000).toFixed(1)}M DA` : "0", color: "bg-green-50 text-green-700" },
            { label: t("employees.title"), value: summary.active_employees ?? "—", color: "bg-blue-50 text-blue-700" },
            { label: t("conventions.title"), value: summary.active_conventions ?? "—", color: "bg-purple-50 text-purple-700" },
          ].map((card, i) => (
            <div key={i} className="card text-center">
              <p className="text-xs font-semibold text-gray-500 mb-1">{card.label}</p>
              <p className={`text-2xl font-black ${card.color}`}>{card.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
