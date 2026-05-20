/**
 * PHOTO UPLOAD — Composant upload/prévisualisation photo
 * Drag & drop + clic + prévisualisation immédiate
 */
import { useCallback, useRef, useState } from "react";
import { Camera, Trash2, Upload, User } from "lucide-react";
import { clsx } from "clsx";
import { useUploadPhoto, useDeletePhoto } from "../hooks/useEmployees";
import { ConfirmDialog } from "@shared/components/ui/index";

interface PhotoUploadProps {
  employeeId: string;
  currentPhotoUrl: string | null;
  employeeName: string;
}

export function PhotoUpload({ employeeId, currentPhotoUrl, employeeName }: PhotoUploadProps) {
  const [preview, setPreview]       = useState<string | null>(null);
  const [dragOver, setDragOver]     = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadPhoto(employeeId);
  const deleteMutation = useDeletePhoto(employeeId);

  const displayUrl = preview ?? currentPhotoUrl;

  const processFile = useCallback(async (file: File) => {
    // Validation client
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      alert("Format non supporté. Utilisez JPEG, PNG ou WebP.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("La photo ne doit pas dépasser 5 Mo.");
      return;
    }
    // Prévisualisation immédiate
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
    // Upload
    await uploadMutation.mutateAsync(file);
    setPreview(null); // laisser la vraie URL s'afficher
  }, [uploadMutation]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = "";
  };

  const handleDelete = async () => {
    await deleteMutation.mutateAsync();
    setPreview(null);
    setShowConfirm(false);
  };

  const isLoading = uploadMutation.isPending || deleteMutation.isPending;

  return (
    <>
      <div className="flex flex-col items-center gap-3">
        {/* Zone photo */}
        <div
          className={clsx(
            "relative w-32 h-32 rounded-2xl border-2 border-dashed transition-all cursor-pointer",
            dragOver ? "border-brand bg-blue-50 scale-105" : "border-gray-300 hover:border-brand hover:bg-gray-50",
            isLoading && "opacity-50 pointer-events-none",
          )}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => fileInputRef.current?.click()}
        >
          {displayUrl ? (
            <>
              <img
                src={displayUrl}
                alt={employeeName}
                className="w-full h-full object-cover rounded-2xl"
              />
              {/* Overlay hover */}
              <div className="absolute inset-0 bg-black/40 rounded-2xl opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center">
                <Camera className="w-6 h-6 text-white" />
              </div>
            </>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2">
              {isLoading ? (
                <div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" />
              ) : (
                <>
                  <User className="w-10 h-10 text-gray-300" />
                  <Upload className="w-4 h-4 text-gray-400" />
                </>
              )}
            </div>
          )}
        </div>

        {/* Boutons */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-300 rounded-lg
              text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <Camera className="w-3.5 h-3.5" />
            {displayUrl ? "Changer" : "Ajouter"}
          </button>
          {displayUrl && (
            <button
              type="button"
              onClick={() => setShowConfirm(true)}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-red-200 rounded-lg
                text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Supprimer
            </button>
          )}
        </div>
        <p className="text-xs text-gray-400 text-center">JPEG, PNG, WebP · Max 5 Mo</p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleFileChange}
      />

      <ConfirmDialog
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleDelete}
        title="Supprimer la photo"
        message="Êtes-vous sûr de vouloir supprimer la photo de cet employé ?"
        confirmLabel="Supprimer"
        loading={deleteMutation.isPending}
      />
    </>
  );
}
