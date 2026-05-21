import { useState } from "react";
import { FileText, Download, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useReports, useGenerateReport, useExports } from "../api/index";
import { Modal, Spinner, Badge } from "@shared/components/ui/index";
import { fmtDateTime, CATEGORY_LABELS } from "../utils/formatters";
import type { ReportCategory, DataExport } from "../types";

export function ReportsPage() {
  const [category, setCategory] = useState<ReportCategory | "">("");
  const [selectedReport, setSelectedReport] = useState<{ id: string; title: string } | null>(null);
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
        || "Erreur lors de la génération du rapport";
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
          <h1 className="text-2xl font-bold text-gray-900">Rapports</h1>
          <p className="text-gray-500 text-sm">Génération de rapports et exports</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowExportsModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Clock className="w-4 h-4" />
            Exports récents
          </button>
          <select value={category} onChange={e => setCategory(e.target.value as ReportCategory | "")}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option value="">Toutes catégories</option>
            {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      {reports.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>Aucun rapport disponible</p>
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
                  <h3 className="text-sm font-semibold text-gray-900 truncate">{report.title}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{report.category_display}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 flex-1 line-clamp-2 mb-3">
                {report.description || "Aucune description"}
              </p>
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  {report.is_system ? "Système" : "Personnalisé"}
                </span>
                <button
                  onClick={() => setSelectedReport({ id: report.id, title: report.title })}
                  disabled={!report.is_active}
                  className="flex items-center gap-1 px-3 py-1.5 bg-brand text-white text-xs rounded-lg hover:bg-brand/90 disabled:opacity-40 font-medium"
                >
                  <Download className="w-3 h-3" /> Générer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Générer un rapport — Modal */}
      <Modal open={!!selectedReport} onClose={() => { setSelectedReport(null); setError(null); }}
        title={`Générer le rapport : ${selectedReport?.title || ""}`} size="sm"
        footer={
          <>
            <button onClick={() => setSelectedReport(null)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              Annuler
            </button>
            <button onClick={handleGenerate} disabled={generateMut.isPending}
              className="px-4 py-2 text-sm bg-brand text-white rounded-lg hover:bg-brand/90 disabled:opacity-50 flex items-center gap-2">
              {generateMut.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Générer
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
            <label className="text-sm font-medium text-gray-700 block mb-1">Format d'export</label>
              <select value={exportFormat} onChange={e => setExportFormat(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option value="csv">CSV</option>
                <option value="excel">Excel (.xlsx)</option>
                <option value="json">JSON</option>
                <option value="pdf">PDF</option>
              </select>
          </div>
          <p className="text-xs text-gray-400">
            Le rapport sera généré en arrière-plan. Vous recevrez une notification et pourrez le télécharger depuis la liste des exports.
          </p>
        </div>
      </Modal>

      {/* Exports récents — Modal */}
      <Modal open={showExportsModal} onClose={() => setShowExportsModal(false)}
        title="Exports récents" size="lg"
      >
        {exportsLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : exports.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Download className="w-10 h-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Aucun export pour le moment</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-gray-500 px-2">
              <span className="w-32">Rapport</span>
              <span className="w-20 text-center">Format</span>
              <span className="w-24 text-center">Statut</span>
              <span className="w-32 text-right">Date</span>
              <span className="w-16 text-right">Action</span>
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
                      <Download className="w-3 h-3" /> Télécharger
                    </a>
                  ) : e.status === "failed" ? (
                    <span className="text-xs text-red-400" title={e.error_message || ""}>Erreur</span>
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
