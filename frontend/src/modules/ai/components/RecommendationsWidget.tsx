import { Lightbulb, ThumbsUp, ThumbsDown, CheckCircle, XCircle, ExternalLink } from "lucide-react";
import { useActiveRecommendations, useRecommendationFeedback } from "../api";

const PRIORITY_COLORS: Record<string, string> = {
  critical: "text-red-600 bg-red-50 border-red-200",
  high: "text-orange-600 bg-orange-50 border-orange-200",
  medium: "text-blue-600 bg-blue-50 border-blue-200",
  low: "text-gray-600 bg-gray-50 border-gray-200",
};

const DOMAIN_ICONS: Record<string, string> = {
  finance: "💰",
  conventions: "📋",
  benefits: "🎁",
  hr: "👥",
};

export function RecommendationsWidget() {
  const { data: recommendations, isLoading } = useActiveRecommendations();
  const { mutate: sendFeedback } = useRecommendationFeedback();

  if (isLoading) return null;
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="w-5 h-5 text-amber-500" />
        <h2 className="text-base font-semibold text-gray-800">
          Recommandations IA
        </h2>
      </div>
      <div className="space-y-3">
        {recommendations.slice(0, 5).map(rec => (
          <div
            key={rec.id}
            className={`rounded-xl border p-3 ${PRIORITY_COLORS[rec.priority] || PRIORITY_COLORS.medium}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-sm">{DOMAIN_ICONS[rec.domain] || "💡"}</span>
                  <span className="text-xs font-medium uppercase opacity-60">{rec.domain}</span>
                  <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                    rec.priority === "critical" ? "bg-red-200" :
                    rec.priority === "high" ? "bg-orange-200" :
                    rec.priority === "medium" ? "bg-blue-200" : "bg-gray-200"
                  }`}>
                    {rec.priority_display}
                  </span>
                </div>
                <p className="text-sm font-semibold truncate">{rec.title}</p>
                {rec.detail && (
                  <p className="text-xs mt-1 opacity-70 line-clamp-2">{rec.detail}</p>
                )}
              </div>
            </div>

            {rec.action_url && (
              <a
                href={rec.action_url}
                className="inline-flex items-center gap-1 text-xs font-medium mt-2 hover:underline"
              >
                <ExternalLink className="w-3 h-3" />
                {rec.action_label || "Voir"}
              </a>
            )}

            {rec.feedback === "pending" && (
              <div className="flex items-center gap-1 mt-2 pt-2 border-t border-current/10">
                <button
                  onClick={() => sendFeedback({ id: rec.id, feedback: "helpful" })}
                  className="p-1 rounded hover:bg-black/10 transition-colors"
                  title="Utile"
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => sendFeedback({ id: rec.id, feedback: "not_helpful" })}
                  className="p-1 rounded hover:bg-black/10 transition-colors"
                  title="Pas utile"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => sendFeedback({ id: rec.id, feedback: "applied" })}
                  className="p-1 rounded hover:bg-black/10 transition-colors"
                  title="Appliquée"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => sendFeedback({ id: rec.id, feedback: "dismissed" })}
                  className="p-1 rounded hover:bg-black/10 transition-colors"
                  title="Ignorer"
                >
                  <XCircle className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
