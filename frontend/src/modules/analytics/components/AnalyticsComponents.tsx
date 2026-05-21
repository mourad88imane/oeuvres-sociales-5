import { AlertTriangle, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { clsx } from "clsx";
import { TREND_UI, KPI_CATEGORY_UI } from "../types";
import { fmtNumber, fmtPct, progressBarClass } from "../utils/formatters";
import type { KpiValue, KpiCategory } from "../types";

interface KpiCardProps {
  kpi: KpiValue;
  onClick?: () => void;
}

export function AnalyticsKpiCard({ kpi, onClick }: KpiCardProps) {
  const trend = TREND_UI[kpi.trend];
  const cat = KPI_CATEGORY_UI[kpi.category as KpiCategory] || { label: kpi.category, color: "#6B7280" };
  const isGood = kpi.trend === "up" && !["expired_conventions", "pending_payments"].includes(kpi.code);
  const isBad = kpi.trend === "down" && !["consumption_rate", "active_rate", "active_employees"].includes(kpi.code);

  return (
    <div onClick={onClick}
      className={clsx("card p-4 border-l-4 transition-shadow hover:shadow-md cursor-pointer",
        kpi.trend === "up" ? "border-l-emerald-400" :
        kpi.trend === "down" ? "border-l-red-400" : "border-l-gray-300"
      )}>
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{cat.label}</span>
        <span className={clsx("text-lg", trend.class)}>{trend.icon}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900 mb-0.5">{fmtNumber(kpi.current_value ?? 0)}</p>
      <p className="text-sm font-medium text-gray-700 truncate">{kpi.name}</p>
      {kpi.unit && <p className="text-xs text-gray-400">{kpi.unit}</p>}
      {kpi.variation != null && (
        <div className={clsx("flex items-center gap-1 mt-2 text-xs font-medium", isBad ? "text-red-600" : isGood ? "text-green-600" : "text-gray-500")}>
          {kpi.variation > 0 ? <TrendingUp className="w-3 h-3" /> : kpi.variation < 0 ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          <span>{kpi.variation > 0 ? "+" : ""}{kpi.variation.toFixed(1)} %</span>
        </div>
      )}
      {kpi.target_value != null && kpi.current_value != null && (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-400 mb-0.5">
            <span>Objectif: {fmtNumber(kpi.target_value)}</span>
            <span>{fmtPct((kpi.current_value / kpi.target_value) * 100)}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div className={clsx("h-full rounded-full", progressBarClass((kpi.current_value / kpi.target_value) * 100))}
              style={{ width: `${Math.min((kpi.current_value / kpi.target_value) * 100, 100)}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  icon?: React.ElementType;
  iconBg?: string;
  iconColor?: string;
  trend?: { value: string; positive: boolean };
  alert?: boolean;
}

export function AnalyticsStatCard({ label, value, sub, icon: Icon, iconBg, iconColor, trend, alert }: StatCardProps) {
  return (
    <div className={clsx("card p-4", alert && "border-l-4 border-l-amber-400")}>
      <div className="flex items-start justify-between mb-2">
        {Icon && (
          <div className={clsx("p-2 rounded-lg", iconBg || "bg-gray-100")}>
            <Icon className={clsx("w-4 h-4", iconColor || "text-gray-600")} />
          </div>
        )}
        {trend && (
          <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full",
            trend.positive ? "text-green-700 bg-green-50" : "text-red-600 bg-red-50"
          )}>{trend.value}</span>
        )}
        {alert && <AlertTriangle className="w-4 h-4 text-amber-500" />}
      </div>
      <p className="text-xl font-bold text-gray-900 mb-0.5">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

interface CategorySummaryProps {
  title: string;
  icon: React.ElementType;
  color: string;
  stats: Array<{ label: string; value: string; alert?: boolean }>;
}

export function CategorySummaryCard({ title, icon: Icon, color, stats }: CategorySummaryProps) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-2 rounded-lg" style={{ background: `${color}15` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </div>
      <div className="space-y-2">
        {stats.map(s => (
          <div key={s.label} className="flex items-center justify-between text-sm">
            <span className="text-gray-500">{s.label}</span>
            <span className={clsx("font-medium", s.alert ? "text-red-600" : "text-gray-900")}>{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface TrendChartTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string; dataKey: string }>;
  label?: string;
  formatter?: (val: number) => string;
}

export function ChartTooltip({ active, payload, label, formatter }: TrendChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-medium text-gray-700 mb-1">{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-500">{p.name}:</span>
          <span className="font-medium text-gray-800">
            {formatter ? formatter(p.value) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

interface ExportButtonProps {
  onExport: (format: string) => void;
  loading?: boolean;
  formats?: string[];
}

export function ExportButton({ onExport, loading, formats = ["csv", "excel"] }: ExportButtonProps) {
  return (
    <div className="flex gap-1.5">
      {formats.map(f => (
        <button key={f} onClick={() => onExport(f)} disabled={loading}
          className="flex items-center gap-1.5 px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50 uppercase font-medium">
          {loading ? "..." : f}
        </button>
      ))}
    </div>
  );
}
