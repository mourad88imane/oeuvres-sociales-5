import { useTranslation } from "react-i18next";
import { AlertTriangle, CheckCircle2, Eye } from "lucide-react";
import { useUnresolvedAnomalies, useResolveAnomaly } from "../api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "border-l-red-500 bg-red-50",
  high: "border-l-orange-500 bg-orange-50",
  medium: "border-l-yellow-500 bg-yellow-50",
  low: "border-l-blue-500 bg-blue-50",
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
};

export function AnomalyFeedWidget() {
  const { t } = useTranslation();
  const { data: anomalies, isLoading } = useUnresolvedAnomalies();
  const { mutate: resolve } = useResolveAnomaly();

  if (isLoading) return null;
  if (!anomalies || anomalies.length === 0) return null;

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-red-500" />
        <h2 className="text-base font-semibold text-gray-800">
          {t("ai.anomalies.title")}
        </h2>
        {anomalies.length > 0 && (
          <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
            {anomalies.length}
          </span>
        )}
      </div>
      <div className="space-y-2 max-h-72 overflow-y-auto">
        {anomalies.slice(0, 10).map(a => (
          <div
            key={a.id}
            className={`border-l-4 rounded-r-xl px-3 py-2 ${SEVERITY_COLORS[a.severity] || SEVERITY_COLORS.medium}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${SEVERITY_BADGE[a.severity] || SEVERITY_BADGE.medium}`}>
                    {a.severity_display}
                  </span>
                  <span className="text-xs text-gray-400">{a.detection_method}</span>
                  <span className="text-xs text-gray-400">{a.time_ago}</span>
                </div>
                <p className="text-sm font-medium truncate">{a.metric_name}</p>
                <p className="text-xs text-gray-500 truncate">{a.target_repr}</p>
                {a.explanation && (
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{a.explanation}</p>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => resolve({ id: a.id, status: "investigating" })}
                  className="p-1 rounded hover:bg-gray-200 transition-colors"
                  title={t("ai.anomalies.investigating")}
                >
                  <Eye className="w-3.5 h-3.5 text-gray-500" />
                </button>
                <button
                  onClick={() => resolve({ id: a.id, status: "resolved", note: t("ai.anomalies.resolvedFromDashboard") })}
                  className="p-1 rounded hover:bg-gray-200 transition-colors"
                  title={t("ai.anomalies.resolve")}
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
