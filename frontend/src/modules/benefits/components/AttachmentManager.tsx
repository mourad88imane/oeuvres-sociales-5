/**
 * ATTACHMENTS MANAGER — Gestion des pièces jointes
 */
import { useRef, useState } from "react";
import { Upload, FileText, Trash2, Download, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import { useUploadAttachment } from "../hooks/useBenefits";
import { ConfirmDialog } from "@shared/components/ui/index";
import { benefitApi } from "../api";
import type { Attachment } from "../types";

const DOC_TYPE_OPTIONS = [
  { value: "prescription",   label: "Ordonnance médicale" },
  { value: "invoice",        label: "Facture" },
  { value: "certificate",    label: "Certificat" },
  { value: "identity",       label: "Pièce d'identité" },
  { value: "salary_slip",    label: "Bulletin de salaire" },
  { value: "bank_details",   label: "RIB bancaire" },
  { value: "other",          label: "Autre document" },
];

const FILE_ICON: Record<string, string> = {
  "application/pdf": "📄",
  "image/jpeg": "🖼️",
  "image/png": "🖼️",
  "image/webp": "🖼️",
  "default": "📎",
};

interface AttachmentManagerProps {
  benefitId: string;
  attachments: Attachment[];
  canUpload?: boolean;
  canDelete?: boolean;
}

export function AttachmentManager({
  benefitId, attachments, canUpload = true, canDelete = true,
}: AttachmentManagerProps) {
  const [dragOver,    setDragOver]    = useState(false);
  const [selectedType,setSelectedType]= useState("other");
  const [description, setDescription]= useState("");
  const [deleteTarget,setDeleteTarget]= useState<string | null>(null);
  const [deleting,    setDeleting]    = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadAttachment(benefitId);

  const handleFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    for (const file of Array.from(files)) {
      await uploadMutation.mutateAsync({
        file, docType: selectedType, description,
      });
    }
    setDescription("");
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await benefitApi.deleteAttachment(benefitId, deleteTarget);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* ── Upload zone ──────────────────────────────── */}
      {canUpload && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Type de document</label>
              <select value={selectedType} onChange={e => setSelectedType(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500">
                {DOC_TYPE_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Description (optionnel)</label>
              <input value={description} onChange={e => setDescription(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Ex : Ordonnance Dr. Kaci" />
            </div>
          </div>

          {/* Drag & drop */}
          <div
            className={clsx(
              "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all",
              dragOver
                ? "border-brand bg-blue-50 scale-[1.01]"
                : "border-gray-200 hover:border-gray-300 hover:bg-gray-50",
              uploadMutation.isPending && "opacity-60 pointer-events-none",
            )}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploadMutation.isPending ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="w-8 h-8 text-brand animate-spin" />
                <p className="text-sm text-gray-500">Téléversement en cours...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="w-8 h-8 text-gray-400" />
                <p className="text-sm font-medium text-gray-600">
                  Glissez vos fichiers ou <span className="text-brand underline">parcourez</span>
                </p>
                <p className="text-xs text-gray-400">PDF, Images, Word · Max 10 Mo par fichier</p>
              </div>
            )}
          </div>
          <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
            className="hidden" onChange={e => handleFiles(e.target.files)} />
        </div>
      )}

      {/* ── Liste ────────────────────────────────────── */}
      {attachments.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <FileText className="w-10 h-10 mx-auto mb-2 opacity-40" />
          <p className="text-sm">Aucune pièce jointe</p>
        </div>
      ) : (
        <div className="space-y-2">
          {attachments.map(att => {
            const icon = FILE_ICON[att.mime_type] ?? FILE_ICON.default;
            return (
              <div key={att.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
                <span className="text-2xl">{icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{att.original_name}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500 flex-wrap">
                    <span className="bg-gray-200 px-1.5 py-0.5 rounded">{att.doc_type_display}</span>
                    <span>{att.file_size_display}</span>
                    {att.description && <span className="italic truncate max-w-xs">{att.description}</span>}
                    {att.uploaded_by_name && <span>par {att.uploaded_by_name}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {att.file_url && (
                    <a href={att.file_url} target="_blank" rel="noreferrer"
                      className="p-1.5 text-gray-400 hover:text-brand hover:bg-blue-50 rounded transition-colors"
                      title="Télécharger">
                      <Download className="w-4 h-4" />
                    </a>
                  )}
                  {canDelete && (
                    <button onClick={() => setDeleteTarget(att.id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      title="Supprimer">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget} onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Supprimer la pièce jointe"
        message="Ce fichier sera définitivement supprimé. Continuer ?"
        confirmLabel="Supprimer" loading={deleting}
      />
    </div>
  );
}
