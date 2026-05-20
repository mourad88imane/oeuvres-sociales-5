import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Building2, Calendar, DollarSign,
  Clock, FileText, AlertTriangle, Upload, Download,
} from "lucide-react";
import { clsx } from "clsx";
import { useConvention, useConventionDocuments, useConventionAlerts } from "../api/index";
import { conventionsApi } from "../api/index";
import {
  ConventionStatusBadge, ConventionActions, ConventionAlertPanel,
} from "../components/ConventionComponents";
import { Spinner, Modal, Field, inputCls } from "@shared/components/ui/index";
import { fmtDZD, fmtDate } from "../utils/formatters";
import { PARTNER_TYPE_UI, CONVENTION_STATUS_UI } from "../types";

export function ConventionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);

  const { data: conv, isLoading } = useConvention(id ?? null);
  const { data: docsData } = useConventionDocuments(id ? { convention_id: id } : {});
  const { data: alertsData } = useConventionAlerts(id ? { convention_id: id, unresolved: "true" } : {});

  const documents = docsData?.results ?? [];
  const alerts = alertsData?.results ?? [];

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = form.querySelector<HTMLInputElement>('input[type="file"]');
    const typeSelect = form.querySelector<HTMLSelectElement>('[name="doc_type"]');
    const descInput = form.querySelector<HTMLTextAreaElement>('[name="description"]');
    if (!fileInput?.files?.[0] || !id) return;

    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    fd.append("doc_type", typeSelect?.value ?? "contract");
    fd.append("description", descInput?.value ?? "");

    setUploading(true);
    try {
      await conventionsApi.uploadDocument(id, fd);
      setShowUpload(false);
      window.location.reload();
    } finally {
      setUploading(false);
    }
  };

  if (isLoading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>;
  if (!conv) return (
    <div className="text-center py-16 text-gray-400">
      <Building2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p>Convention introuvable</p>
    </div>
  );

  const isExpiring = conv.status === "expiring_soon";
  const isExpired = conv.status === "expired";
  const isActive = conv.status === "active";

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Back */}
      <button onClick={() => navigate("/conventions")}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" />Retour aux conventions
      </button>

      {/* Header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {conv.reference}
              </span>
              <ConventionStatusBadge status={conv.status} />
              {isExpiring && (
                <span className="flex items-center gap-1 text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
                  <Clock className="w-3 h-3" />{conv.days_until_expiry} jours restants
                </span>
              )}
            </div>
            <h1 className="text-xl font-bold text-gray-900">{conv.title}</h1>
            <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
              <Building2 className="w-4 h-4" />
              <span>{conv.partner_name} ({conv.partner_code})</span>
            </div>
          </div>
          <ConventionActions convention={conv} />
        </div>

        {conv.description && (
          <p className="text-sm text-gray-600 mt-4 bg-gray-50 rounded-lg p-3">{conv.description}</p>
        )}

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mt-4">
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
            {conv.renewal_mode_display}
          </span>
          {conv.requires_attachments && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              Pièces jointes obligatoires
            </span>
          )}
        </div>
      </div>

      {/* Détails */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-3">
            <Calendar className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Dates</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Date d'effet</span>
              <span className="font-medium">{fmtDate(conv.start_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Échéance</span>
              <span className={clsx("font-medium", isExpired ? "text-red-600" : isExpiring ? "text-amber-600" : "")}>
                {fmtDate(conv.end_date)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Durée</span>
              <span className="font-medium">{conv.duration_display}</span>
            </div>
            {conv.signed_date && (
              <div className="flex justify-between">
                <span className="text-gray-500">Signée le</span>
                <span className="font-medium">{fmtDate(conv.signed_date)}</span>
              </div>
            )}
            {conv.terminated_date && (
              <div className="flex justify-between">
                <span className="text-gray-500">Résiliée le</span>
                <span className="font-medium text-red-600">{fmtDate(conv.terminated_date)}</span>
              </div>
            )}
            {conv.renewed_at && (
              <div className="flex justify-between">
                <span className="text-gray-500">Dernier renouvellement</span>
                <span className="font-medium">{fmtDate(conv.renewed_at)}</span>
              </div>
            )}
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-3">
            <DollarSign className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Financier</span>
          </div>
          {conv.amount != null ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Montant</span>
                <span className="font-bold text-lg">{fmtDZD(conv.amount)}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400">Aucun montant renseigné</p>
          )}
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-3">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">Statut</span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <ConventionStatusBadge status={conv.status} />
            </div>
            {isExpiring && (
              <p className="text-xs text-amber-600">
                Expire dans {conv.days_until_expiry} jour(s)
              </p>
            )}
            {conv.ai_metadata && Object.keys(conv.ai_metadata).length > 0 && (
              <p className="text-xs text-gray-400">Données IA disponibles</p>
            )}
          </div>
        </div>
      </div>

      {/* Documents */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700">
            Documents ({documents.length})
          </h2>
          <button onClick={() => setShowUpload(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-brand text-white text-xs rounded-lg hover:bg-blue-700">
            <Upload className="w-3.5 h-3.5" />Ajouter
          </button>
        </div>
        {documents.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-4">Aucun document</p>
        ) : (
          <div className="space-y-2">
            {documents.map(doc => (
              <div key={doc.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm">
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-800">{doc.original_name}</p>
                    <p className="text-xs text-gray-500">
                      {doc.doc_type_display} · {doc.file_size > 0 ? `${(doc.file_size / 1024).toFixed(0)} KB` : ""} · {fmtDate(doc.created_at)}
                    </p>
                  </div>
                </div>
                {doc.file_url && (
                  <a href={doc.file_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-2.5 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-600 hover:bg-gray-100">
                    <Download className="w-3 h-3" />Télécharger
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alertes */}
      {alerts.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700">Alertes ({alerts.length})</h2>
          </div>
          <ConventionAlertPanel alerts={alerts} maxItems={10} />
        </div>
      )}

      {/* Upload Modal */}
      <Modal open={showUpload} onClose={() => setShowUpload(false)}
        title="Ajouter un document" size="sm"
        footer={
          <>
            <button onClick={() => setShowUpload(false)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Annuler</button>
            <button type="submit" form="upload-form" disabled={uploading}
              className="flex items-center gap-2 px-4 py-2 bg-brand text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-60">
              {uploading && <Spinner size="sm" />}Uploader
            </button>
          </>
        }>
        <form id="upload-form" onSubmit={handleUpload} className="space-y-4">
          <Field label="Type de document" required>
            <select name="doc_type" className={inputCls()}>
              <option value="contract">Contrat signé</option>
              <option value="addendum">Avenant</option>
              <option value="annex">Annexe</option>
              <option value="proof">Justificatif</option>
              <option value="report">Rapport</option>
              <option value="other">Autre</option>
            </select>
          </Field>
          <Field label="Fichier" required>
            <input type="file" className={inputCls()} required accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg" />
          </Field>
          <Field label="Description">
            <textarea name="description" rows={2} className={inputCls()} placeholder="Description optionnelle..." />
          </Field>
        </form>
      </Modal>
    </div>
  );
}
