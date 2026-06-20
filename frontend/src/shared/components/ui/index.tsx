/**
 * COMPOSANTS UI PARTAGÉS
 * Badge, Modal, ConfirmDialog, EmptyState, Spinner, Toast, ErrorBoundary
 */
import * as ToastPrimitive from "@radix-ui/react-toast";
import { useState, useEffect, useRef } from "react";

export { ErrorBoundary } from "./ErrorBoundary";
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
  const variantStyles: Record<string, { color: string; bg: string }> = {
    default: { color: "#8a8882", bg: "rgba(138,136,130,0.1)" },
    success: { color: "#16a34a", bg: "rgba(34,197,94,0.1)" },
    warning: { color: "#d97706", bg: "rgba(245,158,11,0.1)" },
    error:   { color: "#dc2626", bg: "rgba(239,68,68,0.1)" },
    info:    { color: "#3b82f6", bg: "rgba(59,130,246,0.1)" },
    purple:  { color: "#a855f7", bg: "rgba(168,85,247,0.1)" },
  };
  const vs = variantStyles[variant] || variantStyles.default;
  const sz = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1";

  const dotColors: Record<string, string> = {
    success: "#16a34a", warning: "#d97706", error: "#dc2626", info: "#3b82f6", default: "#8a8882",
  };

  return (
    <span className={clsx("inline-flex items-center gap-1 rounded-full font-medium", sz)}
      style={{ color: vs.color, background: vs.bg }}>
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: dotColors[variant] || dotColors.default }} />
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
        "rounded-2xl shadow-2xl w-full flex flex-col max-h-[90vh]",
        sizeClasses[size],
      )}
        style={{
          background: "#ffffff",
          border: "1px solid rgba(0,0,0,0.06)",
          boxShadow: "0 20px 60px -10px rgba(0,0,0,0.1)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid rgba(0,0,0,0.04)" }}>
          <h2 className="text-lg font-bold" style={{ color: "#1a1917" }}>{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors"
            style={{ color: "#8a8882" }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(0,0,0,0.04)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
        {/* Footer */}
        {footer && (
          <div className="px-6 py-4 rounded-b-2xl flex justify-end gap-3"
            style={{
              borderTop: "1px solid rgba(0,0,0,0.04)",
              background: "#f8f7f4",
            }}>
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
            className="px-4 py-2 text-sm border rounded-xl disabled:opacity-50 transition-colors font-bold"
            style={{
              borderColor: "rgba(0,0,0,0.08)",
              color: "#4d4b46",
            }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(0,0,0,0.03)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}>
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
        <p className="text-sm leading-relaxed" style={{ color: "#4d4b46" }}>{message}</p>
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
        <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
          style={{ background: "rgba(0,0,0,0.04)" }}>
          <Icon className="w-8 h-8" style={{ color: "#a8a49a" }} />
        </div>
      )}
      <h3 className="text-base font-bold mb-1" style={{ color: "#1a1917" }}>{title}</h3>
      {description && <p className="text-sm max-w-xs font-medium" style={{ color: "#8a8882" }}>{description}</p>}
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
      <label className="text-sm font-bold" style={{ color: "#4d4b46" }}>
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs" style={{ color: "#8a8882" }}>{hint}</p>}
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
  const borderMap: Record<string, string> = {
    success: "rgba(34, 197, 94, 0.2)",
    error:   "rgba(239, 68, 68, 0.2)",
    info:    "rgba(59, 130, 246, 0.2)",
  };

  return (
    <>
      <ToastPrimitive.Root open={open} onOpenChange={setOpen} duration={4000}
        className="fixed bottom-4 right-4 z-[100] w-80 rounded-2xl shadow-xl p-4 flex items-start gap-3 radix-state-open:animate-slide-up radix-state-closed:animate-fade-out"
        style={{
          background: "#ffffff",
          border: `1px solid ${borderMap[variant]}`,
          boxShadow: "0 10px 30px -8px rgba(0,0,0,0.08)",
        }}>
        <div className="shrink-0 mt-0.5">{iconMap[variant]}</div>
        <div className="flex-1 min-w-0">
          <ToastPrimitive.Title className="text-sm font-bold" style={{ color: "#1a1917" }}>{title}</ToastPrimitive.Title>
          {description && (
            <ToastPrimitive.Description className="text-xs mt-0.5 font-medium" style={{ color: "#8a8882" }}>{description}</ToastPrimitive.Description>
          )}
        </div>
        <ToastPrimitive.Close className="shrink-0 p-0.5" style={{ color: "#a8a49a" }}>
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
    "w-full px-3 py-2 text-sm border rounded-xl transition-colors",
    "focus:outline-none focus:ring-2 focus:ring-brand",
    error
      ? "border-red-400 focus:ring-red-400"
      : "",
  );
