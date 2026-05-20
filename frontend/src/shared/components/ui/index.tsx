/**
 * COMPOSANTS UI PARTAGÉS
 * Badge, Modal, ConfirmDialog, EmptyState, Spinner, Toast
 */
import * as ToastPrimitive from "@radix-ui/react-toast";
import { useState, useEffect, useRef } from "react";
import { X, AlertTriangle, CheckCircle2, Info, Loader2 } from "lucide-react";
import { clsx } from "clsx";

// ═══════════════════════════════════════════════════════
// BADGE
// ═══════════════════════════════════════════════════════
interface BadgeProps {
  variant?: "default" | "success" | "warning" | "error" | "info" | "purple";
  size?: "sm" | "md";
  children: React.ReactNode;
  dot?: boolean;
}

export function Badge({ variant = "default", size = "sm", children, dot }: BadgeProps) {
  const variantClasses: Record<string, string> = {
    default: "bg-gray-100 text-gray-700",
    success: "bg-green-100 text-green-700",
    warning: "bg-amber-100 text-amber-700",
    error:   "bg-red-100 text-red-700",
    info:    "bg-blue-100 text-blue-700",
    purple:  "bg-purple-100 text-purple-700",
  };
  const sizeClasses = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1";

  return (
    <span className={clsx(
      "inline-flex items-center gap-1 rounded-full font-medium",
      variantClasses[variant], sizeClasses,
    )}>
      {dot && (
        <span className={clsx(
          "w-1.5 h-1.5 rounded-full",
          variant === "success" && "bg-green-500",
          variant === "warning" && "bg-amber-500",
          variant === "error"   && "bg-red-500",
          variant === "info"    && "bg-blue-500",
          variant === "default" && "bg-gray-400",
        )} />
      )}
      {children}
    </span>
  );
}

// ═══════════════════════════════════════════════════════
// STATUS BADGE — Spécifique aux statuts employé
// ═══════════════════════════════════════════════════════
const EMPLOYEE_STATUS: Record<string, { label: string; variant: BadgeProps["variant"] }> = {
  active:    { label: "Actif",    variant: "success" },
  inactive:  { label: "Inactif",  variant: "default" },
  retired:   { label: "Retraité", variant: "warning" },
  suspended: { label: "Suspendu", variant: "error"   },
  deceased:  { label: "Décédé",   variant: "default" },
};

export function EmployeeStatusBadge({ status }: { status: string }) {
  const cfg = EMPLOYEE_STATUS[status] ?? { label: status, variant: "default" as const };
  return <Badge variant={cfg.variant} dot>{cfg.label}</Badge>;
}

// ═══════════════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════════════
interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "full";
  footer?: React.ReactNode;
}

export function Modal({ open, onClose, title, children, size = "md", footer }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Fermer avec Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Bloquer le scroll
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  const sizeClasses = {
    sm:   "max-w-sm",
    md:   "max-w-lg",
    lg:   "max-w-2xl",
    xl:   "max-w-4xl",
    full: "max-w-[95vw]",
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className={clsx(
        "bg-white rounded-2xl shadow-2xl w-full flex flex-col max-h-[90vh]",
        sizeClasses[size],
      )}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
        {/* Footer */}
        {footer && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl flex justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// CONFIRM DIALOG
// ═══════════════════════════════════════════════════════
interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "info";
  loading?: boolean;
}

export function ConfirmDialog({
  open, onClose, onConfirm, title, message,
  confirmLabel = "Confirmer", cancelLabel = "Annuler",
  variant = "danger", loading = false,
}: ConfirmDialogProps) {
  const iconMap = {
    danger:  <AlertTriangle className="w-6 h-6 text-red-500" />,
    warning: <AlertTriangle className="w-6 h-6 text-amber-500" />,
    info:    <Info className="w-6 h-6 text-blue-500" />,
  };
  const btnClass = {
    danger:  "bg-red-600 hover:bg-red-700 text-white",
    warning: "bg-amber-500 hover:bg-amber-600 text-white",
    info:    "bg-blue-600 hover:bg-blue-700 text-white",
  };

  return (
    <Modal open={open} onClose={onClose} title={title} size="sm"
      footer={
        <>
          <button onClick={onClose} disabled={loading}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            {cancelLabel}
          </button>
          <button onClick={onConfirm} disabled={loading}
            className={clsx("px-4 py-2 text-sm rounded-lg font-medium flex items-center gap-2 disabled:opacity-50", btnClass[variant])}>
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            {confirmLabel}
          </button>
        </>
      }
    >
      <div className="flex items-start gap-4">
        {iconMap[variant]}
        <p className="text-sm text-gray-600 leading-relaxed">{message}</p>
      </div>
    </Modal>
  );
}

// ═══════════════════════════════════════════════════════
// EMPTY STATE
// ═══════════════════════════════════════════════════════
interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-6">
      {Icon && (
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-gray-400" />
        </div>
      )}
      <h3 className="text-base font-semibold text-gray-800 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-500 max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// SPINNER
// ═══════════════════════════════════════════════════════
export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sz = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-10 h-10" };
  return <Loader2 className={clsx("animate-spin text-brand", sz[size])} />;
}

// ═══════════════════════════════════════════════════════
// FORM FIELD (label + input + erreur)
// ═══════════════════════════════════════════════════════
interface FieldProps {
  label: string;
  error?: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
  className?: string;
}

export function Field({ label, error, required, hint, children, className }: FieldProps) {
  return (
    <div className={clsx("flex flex-col gap-1", className)}>
      <label className="text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-gray-400">{hint}</p>}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// TOAST / NOTIFICATIONS TEMPORAIRES
// ═══════════════════════════════════════════════════════
export function ToastProvider({ children }: { children: React.ReactNode }) {
  return <ToastPrimitive.Provider swipeDirection="right">{children}</ToastPrimitive.Provider>;
}

export function useToast() {
  return {
    success: (title: string, description?: string) => {
      const evt = new CustomEvent("toast", { detail: { title, description, variant: "success" } });
      window.dispatchEvent(evt);
    },
    error: (title: string, description?: string) => {
      const evt = new CustomEvent("toast", { detail: { title, description, variant: "error" } });
      window.dispatchEvent(evt);
    },
    info: (title: string, description?: string) => {
      const evt = new CustomEvent("toast", { detail: { title, description, variant: "info" } });
      window.dispatchEvent(evt);
    },
  };
}

export function ToastViewport() {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [variant, setVariant] = useState<"success" | "error" | "info">("info");

  useEffect(() => {
    const handler = (e: Event) => {
      const { title: t, description: d, variant: v } = (e as CustomEvent).detail;
      setTitle(t); setDescription(d || ""); setVariant(v || "info");
      setOpen(true);
    };
    window.addEventListener("toast", handler);
    return () => window.removeEventListener("toast", handler);
  }, []);

  const iconMap = {
    success: <CheckCircle2 className="w-5 h-5 text-green-500" />,
    error:   <AlertTriangle className="w-5 h-5 text-red-500" />,
    info:    <Info className="w-5 h-5 text-blue-500" />,
  };
  const borderMap = {
    success: "border-green-200",
    error:   "border-red-200",
    info:    "border-blue-200",
  };

  return (
    <>
      <ToastPrimitive.Root open={open} onOpenChange={setOpen} duration={4000}
        className={clsx(
          "fixed bottom-4 right-4 z-[100] w-80 bg-white rounded-xl shadow-xl border p-4 flex items-start gap-3",
          "radix-state-open:animate-slide-up radix-state-closed:animate-fade-out",
          borderMap[variant],
        )}>
        <div className="shrink-0 mt-0.5">{iconMap[variant]}</div>
        <div className="flex-1 min-w-0">
          <ToastPrimitive.Title className="text-sm font-semibold text-gray-900">{title}</ToastPrimitive.Title>
          {description && (
            <ToastPrimitive.Description className="text-xs text-gray-500 mt-0.5">{description}</ToastPrimitive.Description>
          )}
        </div>
        <ToastPrimitive.Close className="shrink-0 p-0.5 text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </ToastPrimitive.Close>
      </ToastPrimitive.Root>
      <ToastPrimitive.Viewport />
    </>
  );
}

// Classe CSS commune pour les inputs
export const inputCls = (error?: string) =>
  clsx(
    "w-full px-3 py-2 text-sm border rounded-lg transition-colors",
    "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
    error
      ? "border-red-400 bg-red-50 focus:ring-red-400"
      : "border-gray-300 bg-white hover:border-gray-400",
  );
