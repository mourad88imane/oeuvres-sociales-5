/**
 * EMPLOYEE HISTORY — Timeline des modifications
 */
import { Clock, Plus, Edit2, Trash2, User } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useEmployeeHistory } from "../hooks/useEmployees";
import { Spinner, EmptyState } from "@shared/components/ui/index";
import type { HistoryRecord } from "../types";

interface EmployeeHistoryProps { employeeId: string; }

export function EmployeeHistory({ employeeId }: EmployeeHistoryProps) {
  const { t } = useTranslation();

  const TYPE_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
    "+": { label: t("employees.historyCreation"),     icon: Plus,   color: "text-green-600", bg: "bg-green-100" },
    "~": { label: t("employees.historyModification"), icon: Edit2,  color: "text-blue-600",  bg: "bg-blue-100"  },
    "-": { label: t("employees.historyDeletion"),     icon: Trash2, color: "text-red-600",   bg: "bg-red-100"   },
  };

  const FIELD_LABELS: Record<string, string> = {
    first_name: t("employees.firstName"), last_name: t("employees.lastName"), job_title: t("employees.jobTitle"),
    status: t("employees.status"), department_id: t("employees.department"), grade: t("employees.grade"),
    grade_level: t("employees.gradeLevel"), contract_type: t("employees.contractType"),
    date_hired: t("employees.dateHired"), base_salary: t("employees.salary"),
    marital_status: t("employees.maritalStatus"), phone: t("employees.phone"),
    email_professional: t("employees.email"), education_level: t("employees.educationLevel"),
    national_id: t("employees.nationalId"), notes: t("common.notes"),
  };

  const { data, isLoading } = useEmployeeHistory(employeeId);

  if (isLoading) return (
    <div className="flex justify-center py-12"><Spinner size="lg" /></div>
  );

  if (!data?.data.length) return (
    <EmptyState icon={Clock} title={t("employees.noHistory")} description={t("employees.noHistoryDescription")} />
  );

  return (
    <div className="space-y-1">
      <p className="text-xs text-gray-400 mb-4">{t("employees.records")}</p>
      <div className="relative">
        {/* Ligne verticale */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />

        <div className="space-y-4">
          {data.data.map((record) => (
            <HistoryEntry key={record.history_id} record={record} />
          ))}
        </div>
      </div>
    </div>
  );
}

function HistoryEntry({ record }: { record: HistoryRecord }) {
  const cfg = TYPE_CONFIG[record.history_type] ?? TYPE_CONFIG["~"];
  const Icon = cfg.icon;
  const date = new Date(record.history_date);

  return (
    <div className="flex gap-4 relative">
      {/* Icône sur la timeline */}
      <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 z-10 ${cfg.bg}`}>
        <Icon className={`w-4 h-4 ${cfg.color}`} />
      </div>

      {/* Contenu */}
      <div className="flex-1 bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold ${cfg.color}`}>{cfg.label}</span>
            {record.history_user && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <User className="w-3 h-3" />
                {record.history_user.name}
              </span>
            )}
          </div>
          <time className="text-xs text-gray-400">
            {date.toLocaleDateString("fr-DZ", { day: "2-digit", month: "short", year: "numeric" })}
            {" — "}
            {date.toLocaleTimeString("fr-DZ", { hour: "2-digit", minute: "2-digit" })}
          </time>
        </div>

        {/* Champs modifiés */}
        {record.changed_fields.length > 0 && (
          <div className="space-y-1.5 mt-2 pt-2 border-t border-gray-100">
            {record.changed_fields.map((change) => (
              <div key={change.field} className="flex items-start gap-2 text-xs">
                <span className="text-gray-500 font-medium min-w-28 shrink-0">
                  {FIELD_LABELS[change.field] ?? change.field}
                </span>
                <div className="flex items-center gap-2 flex-wrap">
                  {change.old != null && (
                    <span className="line-through text-red-400 bg-red-50 px-1.5 py-0.5 rounded">
                      {change.old || t("employees.emptyValue")}
                    </span>
                  )}
                  {change.old != null && <span className="text-gray-400">→</span>}
                  {change.new != null && (
                    <span className="text-green-700 bg-green-50 px-1.5 py-0.5 rounded">
                      {change.new || t("employees.emptyValue")}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
