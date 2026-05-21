/**
 * FINANCE COMPONENTS — BudgetCard, PaymentStatusBadge, ConsumptionBar,
 * AlertPanel, PaymentActions, MarkPaidModal
 */
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  AlertTriangle, CheckCircle2, XCircle,
  Wallet, Loader2,
} from "lucide-react";
import { clsx } from "clsx";
import {
  fmtDZD, fmtPct, fmtDate, consumptionColor,
  progressBarClass,
} from "../utils/formatters";
import {
  useApprovePayment, useApproveBudget, useMarkPaid, useCancelPayment, useResolveAlert,
} from "../api/index";
import { Modal, ConfirmDialog, Field, inputCls } from "@shared/components/ui/index";
import { PAYMENT_STATUS_UI, ALERT_SEVERITY_UI } from "../types";
import type { Budget, Payment, FinancialAlert, PaymentStatus } from "../types";

// ═══════════════════════════════════════════════════════════
// PAYMENT STATUS BADGE
// ═══════════════════════════════════════════════════════════
export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const cfg = PAYMENT_STATUS_UI[status];
  return (
    <span className={clsx("inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full", cfg.badgeClass)}>
      {cfg.label}
    </span>
  );
}

// ═══════════════════════════════════════════════════════════
// CONSUMPTION BAR — Barre de progression budgétaire
// ═══════════════════════════════════════════════════════════
interface ConsumptionBarProps {
  rate:      number;
  showLabel?: boolean;
  height?:   string;
}

export function ConsumptionBar({ rate, showLabel = true, height = "h-2" }: ConsumptionBarProps) {
  const clamped = Math.min(rate, 100);
  const barClass = progressBarClass(rate);
  const textClass = consumptionColor(rate);

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-500">Consommation</span>
          <span className={clsx("text-xs font-bold", textClass)}>
            {fmtPct(rate)}
            {rate >= 100 && " ⚠"}
          </span>
        </div>
      )}
      <div className={clsx("w-full bg-gray-200 rounded-full overflow-hidden", height)}>
        <div
          className={clsx("h-full rounded-full transition-all duration-500", barClass)}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// BUDGET CARD
// ═══════════════════════════════════════════════════════════
interface BudgetCardProps {
  budget:   Budget;
  onApprove?: (id: string) => void;
  compact?:  boolean;
}

export function BudgetCard({ budget, onApprove, compact = false }: BudgetCardProps) {
  const approveMutation = useApproveBudget();

  const borderColor =
    budget.is_overrun        ? "border-l-red-500"    :
    budget.is_alert_triggered ? "border-l-amber-400"  :
    budget.status === "approved" ? "border-l-emerald-400" :
    "border-l-gray-200";

  return (
    <div className={clsx("card p-4 border-l-4 transition-shadow hover:shadow-md", borderColor)}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
              {budget.code}
            </span>
            <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full",
              budget.status === "approved" ? "bg-emerald-100 text-emerald-700" :
              budget.status === "active"   ? "bg-blue-100 text-blue-700"       :
              budget.status === "closed"   ? "bg-gray-100 text-gray-500"       :
              "bg-amber-100 text-amber-700"
            )}>
              {budget.status_display}
            </span>
            {budget.is_overrun && (
              <span className="text-xs text-red-600 font-semibold">⚠ Dépassement</span>
            )}
          </div>
          <p className="font-semibold text-gray-900 mt-1">{budget.label}</p>
          <p className="text-xs text-gray-500">
            {budget.benefit_type_name || budget.department_name || "Global"}
          </p>
        </div>
        {budget.status === "draft" && onApprove && (
          <button
            onClick={() => onApprove(budget.id)}
            disabled={approveMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white text-xs rounded-lg hover:bg-emerald-700 disabled:opacity-60"
          >
            {approveMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
            Approuver
          </button>
        )}
      </div>

      {/* Montants */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-gray-50 rounded-lg px-3 py-2">
          <p className="text-xs text-gray-400">Alloué</p>
          <p className="font-bold text-gray-900 text-sm">{fmtDZD(budget.allocated_amount, true)}</p>
        </div>
        <div className={clsx("rounded-lg px-3 py-2", budget.is_overrun ? "bg-red-50" : "bg-green-50")}>
          <p className="text-xs text-gray-400">Disponible</p>
          <p className={clsx("font-bold text-sm", budget.is_overrun ? "text-red-600" : "text-green-700")}>
            {fmtDZD(budget.available_amount, true)}
          </p>
        </div>
      </div>

      <ConsumptionBar rate={Number(budget.consumption_rate)} />

      {!compact && (
        <div className="mt-3 flex gap-3 text-xs text-gray-500">
          <span>Payé : {fmtDZD(budget.paid_amount, true)}</span>
          <span>•</span>
          <span>Engagé : {fmtDZD(budget.committed_amount, true)}</span>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// PAYMENT ACTIONS
// ═══════════════════════════════════════════════════════════
const markPaidSchema = z.object({
  bank_reference: z.string().min(3, "Référence obligatoire"),
  paid_amount:    z.coerce.number().positive().optional().or(z.literal("")),
  executed_date:  z.string().optional(),
});

const cancelSchema = z.object({
  reason: z.string().min(5, "Motif obligatoire (minimum 5 caractères)"),
});

interface PaymentActionsProps {
  payment:  Payment;
  onUpdate?: () => void;
}

export function PaymentActions({ payment, onUpdate }: PaymentActionsProps) {
  const [showPay,    setShowPay]    = useState(false);
  const [showCancel, setShowCancel] = useState(false);
  const [showApprove,setShowApprove]= useState(false);

  const approveMutation = useApprovePayment();
  const markPaidMut     = useMarkPaid();
  const cancelMut       = useCancelPayment();

  const { register: regPay, handleSubmit: hsPay, formState: { errors: errPay } } =
    useForm({ resolver: zodResolver(markPaidSchema) });
  const { register: regCan, handleSubmit: hsCan, formState: { errors: errCan } } =
    useForm({ resolver: zodResolver(cancelSchema) });

  const handleApprove = async () => {
    await approveMutation.mutateAsync(payment.id);
    setShowApprove(false);
    onUpdate?.();
  };

  const handleMarkPaid = hsPay(async (data) => {
    await markPaidMut.mutateAsync({
      id: payment.id,
      bank_reference: data.bank_reference,
      paid_amount: data.paid_amount ? Number(data.paid_amount) : undefined,
      executed_date: data.executed_date || undefined,
    });
    setShowPay(false);
    onUpdate?.();
  });

  const handleCancel = hsCan(async (data) => {
    await cancelMut.mutateAsync({ id: payment.id, reason: data.reason });
    setShowCancel(false);
    onUpdate?.();
  });

  // Boutons selon le statut
  const canApprove = payment.status === "pending";
  const canPay     = payment.status === "approved";
  const canCancel  = !["paid","reversed","cancelled"].includes(payment.status);

  if (!canApprove && !canPay && !canCancel) return null;

  return (
    <>
      <div className="flex gap-2 flex-wrap">
        {canApprove && (
          <button onClick={() => setShowApprove(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700">
            <CheckCircle2 className="w-3.5 h-3.5" />Approuver
          </button>
        )}
        {canPay && (
          <button onClick={() => setShowPay(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700">
            <Wallet className="w-3.5 h-3.5" />Confirmer le paiement
          </button>
        )}
        {canCancel && (
          <button onClick={() => setShowCancel(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-red-200 text-red-600 text-xs rounded-lg hover:bg-red-50">
            <XCircle className="w-3.5 h-3.5" />Annuler
          </button>
        )}
      </div>

      {/* Approuver */}
      <ConfirmDialog open={showApprove} onClose={() => setShowApprove(false)}
        onConfirm={handleApprove} title="Approuver le paiement"
        message={`Approuver le paiement de ${fmtDZD(payment.amount)} pour ${payment.employee_name} ?`}
        confirmLabel="Approuver" variant="info" loading={approveMutation.isPending} />

      {/* Marquer payé */}
      <Modal open={showPay} onClose={() => setShowPay(false)} title="Confirmer le paiement" size="md"
        footer={
          <>
            <button onClick={() => setShowPay(false)} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Annuler</button>
            <button onClick={handleMarkPaid} disabled={markPaidMut.isPending}
              className="flex items-center gap-2 px-5 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-60">
              {markPaidMut.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Confirmer
            </button>
          </>
        }>
        <div className="space-y-4">
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <p className="text-sm text-green-800">
              <strong>{payment.employee_name}</strong> — {fmtDZD(payment.amount)}
            </p>
            <p className="text-xs text-green-600">{payment.benefit_type_name}</p>
          </div>
          <Field label="Référence bancaire" error={errPay.bank_reference?.message?.toString()} required>
            <input {...regPay("bank_reference")} className={inputCls(errPay.bank_reference?.message?.toString())}
              placeholder="Ex : VIR-2024-00123" />
          </Field>
          <Field label="Montant payé (DZD)" hint={`Montant approuvé : ${fmtDZD(payment.amount)}`}>
            <input type="number" {...regPay("paid_amount")} className={inputCls()} defaultValue={payment.amount} />
          </Field>
          <Field label="Date d'exécution">
            <input type="date" {...regPay("executed_date")} className={inputCls()} />
          </Field>
        </div>
      </Modal>

      {/* Annuler */}
      <Modal open={showCancel} onClose={() => setShowCancel(false)} title="Annuler le paiement" size="sm"
        footer={
          <>
            <button onClick={() => setShowCancel(false)} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Retour</button>
            <button onClick={handleCancel} disabled={cancelMut.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-60">
              {cancelMut.isPending && <Loader2 className="w-4 h-4 animate-spin" />}Annuler le paiement
            </button>
          </>
        }>
        <Field label="Motif d'annulation" error={errCan.reason?.message?.toString()} required>
          <textarea {...regCan("reason")} rows={3} className={inputCls(errCan.reason?.message?.toString())}
            placeholder="Précisez la raison de l'annulation..." />
        </Field>
      </Modal>
    </>
  );
}

// ═══════════════════════════════════════════════════════════
// ALERT PANEL
// ═══════════════════════════════════════════════════════════
interface AlertPanelProps {
  alerts:   FinancialAlert[];
  maxItems?: number;
}

export function AlertPanel({ alerts, maxItems = 5 }: AlertPanelProps) {
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
        const cfg  = ALERT_SEVERITY_UI[alert.severity];
        return (
          <div key={alert.id}
            className={clsx("flex items-start gap-3 p-3 rounded-lg border text-sm", cfg.badgeClass,
              alert.severity === "critical" ? "border-red-200" :
              alert.severity === "warning"  ? "border-amber-200" : "border-blue-200"
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

// ═══════════════════════════════════════════════════════════
// KPI CARD — Carte métrique financière
// ═══════════════════════════════════════════════════════════
interface KpiCardProps {
  label:    string;
  value:    string;
  sub?:     string;
  icon:     React.ElementType;
  iconBg:   string;
  iconColor:string;
  trend?:   { value: string; positive: boolean };
  alert?:   boolean;
}

export function FinanceKpiCard({
  label, value, sub, icon: Icon, iconBg, iconColor, trend, alert,
}: KpiCardProps) {
  return (
    <div className={clsx("card p-5", alert && "border-l-4 border-l-amber-400")}>
      <div className="flex items-start justify-between mb-3">
        <div className={clsx("p-2.5 rounded-xl", iconBg)}>
          <Icon className={clsx("w-5 h-5", iconColor)} />
        </div>
        {trend && (
          <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full",
            trend.positive ? "text-green-700 bg-green-50" : "text-red-600 bg-red-50"
          )}>
            {trend.value}
          </span>
        )}
        {alert && <AlertTriangle className="w-4 h-4 text-amber-500" />}
      </div>
      <p className="text-2xl font-bold text-gray-900 mb-0.5">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}
