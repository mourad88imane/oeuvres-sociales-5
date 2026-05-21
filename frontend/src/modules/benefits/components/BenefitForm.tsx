/**
 * BENEFIT FORM — Création / modification de prestation
 */
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Field, inputCls } from "@shared/components/ui/index";
import { useBenefitTypes } from "../hooks/useBenefits";
import { useEmployees } from "@modules/employees/hooks/useEmployees";
import { CATEGORY_UI, PRIORITY_UI } from "../types";
import type { BenefitCreatePayload, Benefit } from "../types";

const schema = z.object({
  employee:        z.string().uuid("Employé requis"),
  benefit_type:    z.string().uuid("Type de prestation requis"),
  beneficiary:     z.string().uuid().optional().or(z.literal("")),
  title:           z.string().min(5, "Minimum 5 caractères").max(200),
  description:     z.string().optional(),
  requested_amount:z.coerce.number({ invalid_type_error: "Montant requis" }).positive("Doit être positif"),
  priority:        z.enum(["low","normal","high","urgent"]).default("normal"),
  due_date:        z.string().optional(),
  internal_notes:  z.string().optional(),
});

type FormData = z.infer<typeof schema>;

interface BenefitFormProps {
  initialData?: Benefit;
  mode?: "create" | "edit";
  preselectedEmployeeId?: string;
  onSubmit: (data: BenefitCreatePayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function BenefitForm({
  initialData, mode = "create", preselectedEmployeeId,
  onSubmit, onCancel, isLoading,
}: BenefitFormProps) {

  const { data: typesData } = useBenefitTypes({ active_only: true });
  const { data: empData }   = useEmployees({ status: "active", page_size: 200 });
  const types      = typesData?.results ?? [];
  const employees  = empData?.results   ?? [];

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: initialData ? {
      employee:         initialData.employee,
      benefit_type:     initialData.benefit_type,
      beneficiary:      initialData.beneficiary ?? "",
      title:            initialData.title,
      description:      initialData.description,
      requested_amount: initialData.requested_amount,
      priority:         initialData.priority,
      due_date:         initialData.due_date ?? "",
      internal_notes:   initialData.internal_notes,
    } : {
      employee:     preselectedEmployeeId ?? "",
      priority:     "normal",
      benefit_type: "",
    },
  });

  const selectedTypeId = watch("benefit_type");
  const selectedType   = types.find(t => t.id === selectedTypeId);
  const selectedEmpId  = watch("employee");
  const selectedEmp    = employees.find(e => e.id === selectedEmpId);

  const handleFormSubmit = handleSubmit(async (data) => {
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v != null)
    ) as unknown as BenefitCreatePayload;
    await onSubmit(cleaned);
  });

  // Grouper les types par catégorie
  const typesByCategory = types.reduce<Record<string, typeof types>>((acc, t) => {
    if (!acc[t.category]) acc[t.category] = [];
    acc[t.category].push(t);
    return acc;
  }, {});

  return (
    <form onSubmit={handleFormSubmit} className="space-y-5">
      {/* ── Employé et type ──────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Employé" error={errors.employee?.message} required>
          <select {...register("employee")} className={inputCls(errors.employee?.message)}
            disabled={!!preselectedEmployeeId}>
            <option value="">Sélectionner un employé</option>
            {employees.map(e => (
              <option key={e.id} value={e.id}>
                {e.matricule} — {e.full_name}
              </option>
            ))}
          </select>
          {selectedEmp && (
            <p className="text-xs text-gray-500 mt-1">
              {selectedEmp.department_name} · {selectedEmp.job_title} · {selectedEmp.seniority_label}
            </p>
          )}
        </Field>

        <Field label="Type de prestation" error={errors.benefit_type?.message} required>
          <select {...register("benefit_type")} className={inputCls(errors.benefit_type?.message)}>
            <option value="">Sélectionner</option>
            {Object.entries(typesByCategory).map(([cat, catTypes]) => (
              <optgroup key={cat} label={`${CATEGORY_UI[cat as keyof typeof CATEGORY_UI]?.icon} ${CATEGORY_UI[cat as keyof typeof CATEGORY_UI]?.label ?? cat}`}>
                {catTypes.map(t => (
                  <option key={t.id} value={t.id}>
                    {t.name}{t.max_amount ? ` (plafond: ${t.max_amount.toLocaleString("fr-DZ")} DZD)` : ""}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          {/* Info type sélectionné */}
          {selectedType && (
            <div className="mt-2 p-3 bg-blue-50 rounded-lg text-xs text-blue-800 space-y-1">
              {selectedType.max_amount && (
                <p>💰 Plafond : <strong>{selectedType.max_amount.toLocaleString("fr-DZ")} DZD</strong></p>
              )}
              {selectedType.min_seniority_years && (
                <p>📅 Ancienneté minimale : <strong>{selectedType.min_seniority_years} an(s)</strong></p>
              )}
              {selectedType.requires_attachments && (
                <p>📎 Pièces justificatives requises : {selectedType.required_attachments_description || "Voir les conditions"}</p>
              )}
              {selectedType.target_processing_days && (
                <p>⏱ Délai cible : <strong>{selectedType.target_processing_days} jour(s)</strong></p>
              )}
            </div>
          )}
        </Field>
      </div>

      {/* ── Objet et description ─────────────────────── */}
      <Field label="Objet de la demande" error={errors.title?.message} required>
        <input {...register("title")} className={inputCls(errors.title?.message)}
          placeholder="Ex : Consultation spécialiste cardiologue" />
      </Field>

      <Field label="Description / Justification">
        <textarea {...register("description")} rows={3}
          className={inputCls()}
          placeholder="Décrivez le contexte et la justification de votre demande..." />
      </Field>

      {/* ── Montant, priorité, échéance ──────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Field label="Montant demandé (DZD)" error={errors.requested_amount?.message} required>
          <div className="relative">
            <input type="number" step="100" min="0"
              {...register("requested_amount")}
              className={inputCls(errors.requested_amount?.message)}
              placeholder="0" />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">DZD</span>
          </div>
          {selectedType?.max_amount && (
            <p className="text-xs text-gray-400">Plafond : {selectedType.max_amount.toLocaleString("fr-DZ")} DZD</p>
          )}
        </Field>

        <Field label="Priorité">
          <select {...register("priority")} className={inputCls()}>
            {Object.entries(PRIORITY_UI).map(([p, cfg]) => (
              <option key={p} value={p}>{cfg.label}</option>
            ))}
          </select>
        </Field>

        <Field label="Date d'échéance souhaitée">
          <input type="date" {...register("due_date")} className={inputCls()} />
        </Field>
      </div>

      {/* ── Notes internes ───────────────────────────── */}
      <Field label="Notes internes" hint="Visibles uniquement par le personnel de traitement">
        <textarea {...register("internal_notes")} rows={2} className={inputCls()} />
      </Field>

      {/* ── Actions ──────────────────────────────────── */}
      <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
          Annuler
        </button>
        <button type="submit" disabled={isLoading}
          className="flex items-center gap-2 px-5 py-2 bg-brand text-white text-sm rounded-lg hover:bg-brand-light disabled:opacity-60">
          {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
          {mode === "create" ? "Créer la demande" : "Enregistrer"}
        </button>
      </div>
    </form>
  );
}
