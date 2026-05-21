import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import {
  Lightbulb, TrendingUp, Building2, Gift, Wallet, Users,
  RefreshCw, ChevronDown, ChevronUp,
} from "lucide-react";
import { clsx } from "clsx";
import apiClient from "@shared/api/apiClient";
import { Spinner, Badge } from "@shared/components/ui/index";

interface Decision {
  domain: string;
  priority: string;
  title: string;
  detail: string;
}

interface DecisionResponse {
  status: string;
  data: {
    generated_at: string;
    total_recommendations: number;
    recommendations: Decision[];
  };
}

const DOMAIN_ICONS: Record<string, React.ElementType> = {
  finance: Wallet,
  conventions: Building2,
  benefits: Gift,
  hr: Users,
  global: TrendingUp,
};

const PRIORITY_COLORS: Record<string, { labelKey: string; variant: "error" | "warning" | "info" | "default" }> = {
  high:   { labelKey: "ai.decisions.priorityHigh", variant: "error" },
  medium: { labelKey: "ai.decisions.priorityMedium",   variant: "warning" },
  low:    { labelKey: "ai.decisions.priorityLow",  variant: "info" },
};

export function DecisionSupportPage() {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data, isLoading, refetch, isFetching } = useQuery<DecisionResponse>({
    queryKey: ["ai", "decisions"],
    queryFn: () =>
      apiClient.get("/reporting/analytics/decisions/").then(r => r.data),
    staleTime: 1000 * 60 * 2,
  });

  const recommendations = data?.data?.recommendations ?? [];

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t("ai.decisions.title")}</h1>
          <p className="text-gray-500 text-sm">
            {data?.data?.total_recommendations
              ? `${data.data.total_recommendations} ${t("ai.decisions.totalRecommendations")} · ${t("ai.decisions.generatedAt")} ${data.data.generated_at}`
              : t("ai.decisions.smartAnalysis")}
          </p>
        </div>
        <button onClick={() => refetch()}
          className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
          <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
          {t("common.refresh")}
        </button>
      </div>

      {/* Summary banner */}
      <div className="bg-gradient-to-r from-brand to-blue-800 text-white rounded-xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <Lightbulb className="w-8 h-8 text-yellow-300" />
          <div>
            <h2 className="text-lg font-bold">{t("ai.decisions.dashboard")}</h2>
            <p className="text-blue-200 text-sm">
              {t("ai.decisions.realtimeAnalysis")}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center">
            <p className="text-2xl font-bold">{recommendations.length}</p>
            <p className="text-xs text-blue-200">{t("ai.recommendations.title")}</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">
              {recommendations.filter(r => r.priority === "high").length}
            </p>
            <p className="text-xs text-red-300">{t("ai.decisions.priority")}</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">
              {[...new Set(recommendations.map(r => r.domain))].length}
            </p>
            <p className="text-xs text-blue-200">{t("ai.decisions.domains")}</p>
          </div>
        </div>
      </div>

      {/* Recommendations list */}
      {recommendations.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Lightbulb className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>{t("ai.decisions.noRecommendations")}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {recommendations.map((rec, i) => {
            const Icon = DOMAIN_ICONS[rec.domain] || Lightbulb;
            const priority = PRIORITY_COLORS[rec.priority] || PRIORITY_COLORS.low;
            const isExpanded = expanded === `${i}`;

            return (
              <div key={i} className={clsx(
                "card overflow-hidden transition-all",
                rec.priority === "high" && "border-l-4 border-l-red-400",
                rec.priority === "medium" && "border-l-4 border-l-amber-400",
              )}>
                <button onClick={() => setExpanded(isExpanded ? null : `${i}`)}
                  className="w-full flex items-start gap-3 p-4 text-left">
                  <div className={clsx(
                    "p-2 rounded-lg shrink-0",
                    rec.priority === "high" ? "bg-red-50" :
                    rec.priority === "medium" ? "bg-amber-50" : "bg-blue-50",
                  )}>
                    <Icon className={clsx(
                      "w-4 h-4",
                      rec.priority === "high" ? "text-red-500" :
                      rec.priority === "medium" ? "text-amber-500" : "text-blue-500",
                    )} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900 text-sm">{rec.title}</span>
                      <Badge variant={priority.variant}>{t(priority.labelKey)}</Badge>
                    </div>
                    {isExpanded && (
                      <p className="text-sm text-gray-600 mt-2 leading-relaxed">{rec.detail}</p>
                    )}
                  </div>
                  {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
