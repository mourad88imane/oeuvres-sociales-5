import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Building2, CheckCircle2, XCircle, AlertTriangle,
  AlertCircle, Clock, Loader2, FileText,
} from "lucide-react";
import { clsx } from "clsx";
import { fmtDate, fmtDZD } from "../utils/formatters";
import {
  useRenewConvention, useTerminateConvention, useResolveAlert,
} from "../api/index";
import { Modal, ConfirmDialog, Field, inputCls } from "@shared/components/ui/index";
import { CONVENTION_STATUS_UI, ALERT_SEVERITY_UI } from "../types";
import type { Convention, ConventionAlert, ConventionStatus } from "../types";

export function ConventionStatusBadge({ status }: { status: ConventionStatus }) {
  const cfg = CONVENTION_STATUS_UI[status];
  return (
    <span className={clsx("inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full", cfg.badgeClass)}>
      {cfg.label}
    </span>
  );
}

interface KpiCardProps {
  label:     string;
  value:     string;
  sub?:      string;
  icon:      React.ElementType;
  iconBg:    string;
  iconColor: string;
  alert?:    boolean;
}

export function ConventionKpiCard({
  label, value, sub, icon: Icon, iconBg, iconColor, alert,
}: KpiCardProps) {
  return (
    <div className={clsx("card p-5", alert && "border-l-4 border-l-amber-400")}>
      <div className="flex items-start justify-between mb-3">
        <div className={clsx("p-2.5 rounded-xl", iconBg)}>
          <Icon className={clsx("w-5 h-5", iconColor)} />
        </div>
        {alert && <AlertTriangle className="w-4 h-4 text-amber-500" />}
      </div>
      <p className="text-2xl font-bold text-gray-900 mb-0.5">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

interface ConventionCardProps {
  convention: Convention;
}

export function ConventionCard({ convention }: ConventionCardProps) {
  const borderColor =
    convention.status === "expired"       ? "border-l-red-500" :
    convention.status === "expiring_soon"  ? "border-l-amber-400" :
    convention.status === "active"         ? "border-l-emerald-400" :
    convention.status === "terminated"     ? "border-l-gray-400" :
    "border-l-gray-200";

  return (
    <div className={clsx("card p-4 border-l-4 transition-shadow hover:shadow-md", borderColor)}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
              {convention.reference}
            </span>
            <ConventionStatusBadge status={convention.status} />
            {convention.is_expiring_soon && (
              <span className="text-xs text-amber-600 font-semibold">⏳ {convention.days_until_expiry} j</span>
            )}
          </div>
          <p className="font-semibold text-gray-900 mt-1">{convention.title}</p>
          <p className="text-xs text-gray-500">{convention.partner_name}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <div className="bg-gray-50 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-400">Date d'effet</p>
          <p className="font-medium text-gray-900 text-sm">{fmtDate(convention.start_date)}</p>
        </div>
        <div className="bg-gray-50 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-400">Échéance</p>
          <p className="font-medium text-gray-900 text-sm">{fmtDate(convention.end_date)}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Durée : {convention.duration_display}</span>
        {convention.amount != null && <span className="font-medium">{fmtDZD(convention.amount, true)}</span>}
      </div>
    </div>
  );
}

interface AlertPanelProps {
  alerts:   ConventionAlert[];
  maxItems?: number;
}

export function ConventionAlertPanel({ alerts, maxItems = 5 }: AlertPanelProps) {
  const resolveMutation = useResolveAlert();
  const visible = alerts.slice(0, maxItems);

  if (visible.length === 0) {
    return (
      <div className="text-center py-6 text-gray-400 text-sm">
        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 opacity-40" />
        Aucune alerte active
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {visible.map(alert => {
        const cfg = ALERT_SEVERITY_UI[alert.severity];
        return (
          <div key={alert.id}
            className={clsx("flex items-start gap-3 p-3 rounded-lg border text-sm", cfg.badgeClass,
              alert.severity === "critical" ? "border-red-200" :
              alert.severity === "high"     ? "border-orange-200" :
              alert.severity === "medium"   ? "border-amber-200" : "border-blue-200"
            )}>
            <span className="text-base shrink-0">{cfg.icon}</span>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{alert.title}</p>
              <p className="text-xs opacity-80 mt-0.5 line-clamp-2">{alert.message}</p>
              <p className="text-xs opacity-60 mt-1">{fmtDate(alert.created_at)}</p>
            </div>
            {!alert.is_resolved && (
              <button onClick={() => resolveMutation.mutate(alert.id)}
                disabled={resolveMutation.isPending}
                className="text-xs underline opacity-70 hover:opacity-100 shrink-0">
                Résoudre
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

const renewSchema = z.object({
  new_end_date: z.string().min(1, "Date obligatoire"),
  new_amount: z.coerce.number().positive().optional().or(z.literal("")),
  notes: z.string().optional(),
});

const terminateSchema = z.object({
  terminated_date: z.string().optional(),
  reason: z.string().min(5, "Motif obligatoire (min 5 car.)"),
});

interface ConventionActionsProps {
  convention: Convention;
  onUpdate?: () => void;
}

export function ConventionActions({ convention, onUpdate }: ConventionActionsProps) {
  const [showRenew, setShowRenew] = useState(false);
  const [showTerminate, setShowTerminate] = useState(false);

  const renewMut = useRenewConvention();
  const terminateMut = useTerminateConvention();

  const { register: regRenew, handleSubmit: hsRenew, formState: { errors: errRenew } } =
    useForm({ resolver: zodResolver(renewSchema) });
  const { register: regTerm, handleSubmit: hsTerm, formState: { errors: errTerm } } =
    useForm({ resolver: zodResolver(terminateSchema) });

  const canRenew = ["active", "expiring_soon", "expired"].includes(convention.status);
  const canTerminate = !["terminated", "expired"].includes(convention.status);

  const handleRenew = hsRenew(async (data) => {
    await renewMut.mutateAsync({
      id: convention.id,
      new_end_date: data.new_end_date,
      new_amount: data.new_amount ? Number(data.new_amount) : null,
      notes: data.notes,
    });
    setShowRenew(false);
    onUpdate?.();
  });

  const handleTerminate = hsTerm(async (data) => {
    await terminateMut.mutateAsync({
      id: convention.id,
      terminated_date: data.terminated_date || undefined,
      reason: data.reason,
    });
    setShowTerminate(false);
    onUpdate?.();
  });

  if (!canRenew && !canTerminate) return null;

  return (
    <>
      <div className="flex gap-2 flex-wrap">
        {canRenew && (
          <button onClick={() => setShowRenew(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700">
            <CheckCircle2 className="w-3.5 h-3.5" />Renouveler
          </button>
        )}
        {canTerminate && (
          <button onClick={() => setShowTerminate(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-red-200 text-red-600 text-xs rounded-lg hover:bg-red-50">
            <XCircle className="w-3.5 h-3.5" />Résilier
          </button>
        )}
      </div>

      <Modal open={showRenew} onClose={() => setShowRenew(false)}
        title={`Renouveler — ${convention.reference}`} size="md"
        footer={
          <>
            <button onClick={() => setShowRenew(false)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Annuler</button>
            <button onClick={handleRenew} disabled={renewMut.isPending}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-60">
              {renewMut.isPending && <Loader2 className="w-4 h-4 animate-spin" />}Renouveler
            </button>
          </>
        }>
        <div className="space-y-4">
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              <strong>{convention.reference}</strong> — {convention.partner_name}
            </p>
            <p className="text-xs text-blue-600">Échéance actuelle : {fmtDate(convention.end_date)}</p>
          </div>
          <Field label="Nouvelle date d'échéance" error={errRenew.new_end_date?.message} required>
            <input type="date" {...regRenew("new_end_date")} className={inputCls(errRenew.new_end_date?.message)} />
          </Field>
          <Field label="Nouveau montant (DZD)" hint="Optionnel">
            <input type="number" {...regRenew("new_amount")} className={inputCls()} defaultValue={convention.amount ?? ""} />
          </Field>
          <Field label="Notes">
            <textarea {...regRenew("notes")} rows={3} className={inputCls()} placeholder="Notes sur le renouvellement..." />
          </Field>
        </div>
      </Modal>

      <Modal open={showTerminate} onClose={() => setShowTerminate(false)}
        title={`Résilier — ${convention.reference}`} size="sm"
        footer={
          <>
            <button onClick={() => setShowTerminate(false)}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Retour</button>
            <button onClick={handleTerminate} disabled={terminateMut.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-60">
              {terminateMut.isPending && <Loader2 className="w-4 h-4 animate-spin" />}Résilier
            </button>
          </>
        }>
        <Field label="Date de résiliation">
          <input type="date" {...regTerm("terminated_date")} className={inputCls()} />
        </Field>
        <Field label="Motif" error={errTerm.reason?.message} required>
          <textarea {...regTerm("reason")} rows={3} className={inputCls(errTerm.reason?.message)}
            placeholder="Précisez la raison de la résiliation..." />
        </Field>
      </Modal>
    </>
  );
}
