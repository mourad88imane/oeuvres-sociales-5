import { useTranslation } from "react-i18next";
import { HeartPulse, CheckCircle2, XCircle, Syringe, Scan, Stethoscope } from "lucide-react";
import { useMedicalCoverageStatistics, useMedicalCoverageTypes } from "../api";
import { Spinner } from "@shared/components/ui/index";

const TYPE_ICONS: Record<string, React.ElementType> = {
  analysis: Syringe,
  imaging: Scan,
  center: Stethoscope,
};

export function MedicalCoverageWidget() {
  const { t } = useTranslation();
  const { data: stats, isLoading: statsLoading } = useMedicalCoverageStatistics();
  const { data: types, isLoading: typesLoading } = useMedicalCoverageTypes();

  if (statsLoading || typesLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="md" />
      </div>
    );
  }

  if (!stats) return null;

  const pendingStates = ["draft", "submitted"];
  const pending = pendingStates.reduce((acc, s) => acc + (stats.by_status[s] || 0), 0);

  return (
    <div className="bg-white rounded-[32px] p-6" style={{ border: "1px solid rgba(0,0,0,0.04)" }}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ background: "rgba(236,72,153,0.1)" }}>
          <HeartPulse className="w-5 h-5" style={{ color: "#ec4899" }} />
        </div>
        <div>
          <h2 className="text-base font-black" style={{ color: "#1a1917" }}>
            {t("dashboard.medicalCoverage")}
          </h2>
          <p className="text-xs font-medium mt-0.5" style={{ color: "#8a8882" }}>
            {stats.total} {t("dashboard.medicalTotal")}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="rounded-2xl p-3 text-center" style={{ background: "rgba(34,197,94,0.08)" }}>
          <CheckCircle2 className="w-4 h-4 mx-auto mb-1" style={{ color: "#16a34a" }} />
          <p className="text-lg font-black" style={{ color: "#16a34a" }}>{stats.consumed}</p>
          <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "#16a34a" }}>{t("dashboard.medicalConsumed")}</p>
        </div>
        <div className="rounded-2xl p-3 text-center" style={{ background: "rgba(59,130,246,0.08)" }}>
          <CheckCircle2 className="w-4 h-4 mx-auto mb-1" style={{ color: "#3b82f6" }} />
          <p className="text-lg font-black" style={{ color: "#3b82f6" }}>{stats.approved}</p>
          <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: "#3b82f6" }}>{t("dashboard.medicalApproved")}</p>
        </div>
        <div className="rounded-2xl p-3 text-center" style={{ background: pending > 0 ? "rgba(245,158,11,0.08)" : "rgba(138,136,130,0.06)" }}>
          <HeartPulse className="w-4 h-4 mx-auto mb-1" style={{ color: pending > 0 ? "#d97706" : "#8a8882" }} />
          <p className="text-lg font-black" style={{ color: pending > 0 ? "#d97706" : "#8a8882" }}>{pending}</p>
          <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: pending > 0 ? "#d97706" : "#8a8882" }}>{t("dashboard.medicalPending")}</p>
        </div>
      </div>

      {stats.by_type.length > 0 && (
        <div className="space-y-3">
          {stats.by_type.map((bt) => {
            const Icon = TYPE_ICONS[bt.coverage_type__code];
            const typeDef = types?.find((t) => t.code === bt.coverage_type__code);
            const color = typeDef?.color || "#8a8882";
            const pct = stats.total > 0 ? Math.round((bt.count / stats.total) * 100) : 0;
            return (
              <div key={bt.coverage_type__code} className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: `${color}12` }}
                >
                  {Icon ? <Icon className="w-4 h-4" style={{ color }} /> : <HeartPulse className="w-4 h-4" style={{ color }} />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold truncate" style={{ color: "#1a1917" }}>{bt.coverage_type__name}</span>
                    <span className="text-xs font-black" style={{ color: "#8a8882" }}>{bt.count}</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(0,0,0,0.04)" }}>
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}, ${color}88)` }} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {stats.rejected > 0 && (
        <div className="flex items-center gap-2 mt-4 pt-4" style={{ borderTop: "1px solid rgba(0,0,0,0.04)" }}>
          <XCircle className="w-4 h-4" style={{ color: "#dc2626" }} />
          <span className="text-xs font-bold" style={{ color: "#dc2626" }}>
            {stats.rejected} {t("dashboard.medicalRejected")}
          </span>
        </div>
      )}
    </div>
  );
}
