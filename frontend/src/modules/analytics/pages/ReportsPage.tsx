import { useState } from "react";
import { FileText, Download, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useReports, useGenerateReport, useExports } from "../api/index";
import { Modal, Spinner, Badge } from "@shared/components/ui/index";
import { fmtDateTime } from "../utils/formatters";
import type { ReportCategory, DataExport } from "../types";

const CATEGORIES: ReportCategory[] = ["hr", "finance", "benefits", "conventions", "employees", "kpi", "custom"];

export function ReportsPage() {
  const { t } = useTranslation();
  const [category, setCategory] = useState<ReportCategory | "">("");
  const [selectedReport, setSelectedReport] = useState<{ id: string; title: string; code: string } | null>(null);
  const [exportFormat, setExportFormat] = useState<string>("csv");
  const [showExportsModal, setShowExportsModal] = useState(false);

  const { data: reportsData, isLoading } = useReports(category);
  const { data: exportsData, isLoading: exportsLoading } = useExports({ limit: 20 }, showExportsModal);
  const generateMut = useGenerateReport();

  const reports = reportsData?.results || [];
  const exports = exportsData?.results || [];

  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!selectedReport) return;
    setError(null);
    try {
      await generateMut.mutateAsync({ id: selectedReport.id, format: exportFormat });
      setSelectedReport(null);
      setShowExportsModal(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
        || (err as Error)?.message
        || t("reports.error");
      setError(msg);
    }
  };

  const statusBadge = (e: DataExport) => {
    const map: Record<string, { variant: "success" | "error" | "warning" | "info" | "default"; icon: React.ElementType }> = {
      completed: { variant: "success", icon: CheckCircle2 },
      failed:    { variant: "error",   icon: XCircle },
      processing:{ variant: "warning", icon: Loader2 },
      pending:   { variant: "info",    icon: Clock },
    };
    const m = map[e.status] || map.pending;
    const Icon = m.icon;
    return <Badge variant={m.variant}><Icon className="w-3 h-3" /> {e.status_display}</Badge>;
  };

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t("reports.title")}</h1>
          <p className="text-gray-500 text-sm">{t("reports.subtitle")}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowExportsModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Clock className="w-4 h-4" />
            {t("reports.recentExports")}
          </button>
          <select value={category} onChange={e => setCategory(e.target.value as ReportCategory | "")}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option value="">{t("reports.allCategories")}</option>
            {CATEGORIES.filter(k => k !== "custom").map(k => (
              <option key={k} value={k}>{t(`reports.category${k.charAt(0).toUpperCase() + k.slice(1)}`)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      {reports.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>{t("reports.noReports")}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {reports.map(report => (
            <div key={report.id} className="card p-5 flex flex-col">
              <div className="flex items-start gap-3 mb-3">
                <div className="p-2 rounded-lg bg-blue-100 shrink-0">
                  <FileText className="w-4 h-4 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-gray-900 truncate">
                    {t(`reports.list.${report.code}`, { defaultValue: report.title })}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">{report.category_display}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 flex-1 line-clamp-2 mb-3">
                {t(`reports.list.${report.code}_desc`, { defaultValue: report.description || t("reports.noDescription") })}
              </p>
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  {report.is_system ? t("reports.system") : t("reports.custom")}
                </span>
                <button
                  onClick={() => setSelectedReport({ id: report.id, title: report.title, code: report.code })}
                  disabled={!report.is_active}
                  className="flex items-center gap-1 px-3 py-1.5 bg-brand text-white text-xs rounded-lg hover:bg-brand/90 disabled:opacity-40 font-medium"
                >
                  <Download className="w-3 h-3" /> {t("reports.generate")}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Générer un rapport — Modal */}
      <Modal open={!!selectedReport} onClose={() => { setSelectedReport(null); setError(null); }}
        title={t("reports.generateTitle", { title: selectedReport?.code ? t(`reports.list.${selectedReport.code}`, { defaultValue: selectedReport.title }) : selectedReport?.title || "" })} size="sm"
        footer={
          <>
            <button onClick={() => setSelectedReport(null)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              {t("app.cancel")}
            </button>
            <button onClick={handleGenerate} disabled={generateMut.isPending}
              className="px-4 py-2 text-sm bg-brand text-white rounded-lg hover:bg-brand/90 disabled:opacity-50 flex items-center gap-2">
              {generateMut.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {t("reports.generate")}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          {error && (
            <div className="px-3 py-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
              {error}
            </div>
          )}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">{t("reports.exportFormat")}</label>
              <select value={exportFormat} onChange={e => setExportFormat(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option value="csv">{t("reports.formatCsv")}</option>
                <option value="excel">{t("reports.formatExcel")}</option>
                <option value="json">{t("reports.formatJson")}</option>
                <option value="pdf">{t("reports.formatPdf")}</option>
              </select>
          </div>
          <p className="text-xs text-gray-400">
            {t("reports.backgroundInfo")}
          </p>
        </div>
      </Modal>

      {/* Exports récents — Modal */}
      <Modal open={showExportsModal} onClose={() => setShowExportsModal(false)}
        title={t("reports.recentExportsTitle")} size="lg"
      >
        {exportsLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : exports.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Download className="w-10 h-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm">{t("reports.noExports")}</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-gray-500 px-2">
              <span className="w-32">{t("reports.reportCol")}</span>
              <span className="w-20 text-center">{t("reports.formatCol")}</span>
              <span className="w-24 text-center">{t("reports.statusCol")}</span>
              <span className="w-32 text-right">{t("reports.dateCol")}</span>
              <span className="w-16 text-right">{t("reports.actionCol")}</span>
            </div>
            {exports.map(e => (
              <div key={e.id} className="flex items-center justify-between px-3 py-2.5 bg-gray-50 rounded-lg text-sm">
                <span className="w-32 truncate text-gray-800 font-medium">{e.report_title || "—"}</span>
                <span className="w-20 text-center text-xs uppercase text-gray-500">{e.export_format}</span>
                <span className="w-24 flex justify-center">{statusBadge(e)}</span>
                <span className="w-32 text-right text-xs text-gray-400">{fmtDateTime(e.created_at)}</span>
                <span className="w-16 text-right">
                  {e.status === "completed" && e.download_url ? (
                    <a href={e.download_url} target="_blank" rel="noopener noreferrer"
                      className="text-brand hover:underline text-xs flex items-center justify-end gap-1">
                      <Download className="w-3 h-3" /> {t("reports.download")}
                    </a>
                  ) : e.status === "failed" ? (
                    <span className="text-xs text-red-400" title={e.error_message || ""}>{t("reports.errorStatus")}</span>
                  ) : (
                    <span className="text-xs text-gray-400">—</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
}
