/**
 * BENEFICIARY FORM — Formulaire ajout/modification ayant droit
 */
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Field, inputCls } from "@shared/components/ui/index";
import type { Beneficiary, BeneficiaryCreatePayload } from "../types";

const schema = z.object({
  first_name:    z.string().min(2, "Minimum 2 caractères"),
  last_name:     z.string().min(2, "Minimum 2 caractères"),
  first_name_ar: z.string().optional(),
  last_name_ar:  z.string().optional(),
  gender:        z.enum(["M", "F"], { required_error: "Champ obligatoire" }),
  date_of_birth: z.string().min(1, "Champ obligatoire").refine(
    (d) => new Date(d) < new Date(), "La date doit être dans le passé"
  ),
  national_id:  z.string().max(20).optional(),
  relationship: z.enum(["spouse","child","parent","sibling","other"], { required_error: "Champ obligatoire" }),
  is_student:     z.boolean().optional(),
  is_handicapped: z.boolean().optional(),
  school_name:   z.string().optional(),
  school_year:   z.string().optional(),
  spouse_is_employed: z.boolean().nullable().optional(),
  spouse_employer: z.string().optional(),
  birth_certificate_uploaded:    z.boolean().optional(),
  marriage_certificate_uploaded: z.boolean().optional(),
  notes: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

interface BeneficiaryFormProps {
  initialData?: Beneficiary;
  onSubmit: (data: BeneficiaryCreatePayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function BeneficiaryForm({ initialData, onSubmit, onCancel, isLoading }: BeneficiaryFormProps) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: initialData ? {
      first_name: initialData.first_name, last_name: initialData.last_name,
      first_name_ar: initialData.first_name_ar, last_name_ar: initialData.last_name_ar,
      gender: initialData.gender, date_of_birth: initialData.date_of_birth,
      national_id: initialData.national_id,
      relationship: initialData.relationship as FormData["relationship"],
      is_student: initialData.is_student, is_handicapped: initialData.is_handicapped,
      school_name: initialData.school_name, school_year: initialData.school_year,
      notes: initialData.notes,
    } : {},
  });

  const relationship = watch("relationship");
  const isChild   = relationship === "child";
  const isSpouse  = relationship === "spouse";

  const submit = handleSubmit(async (data) => {
    await onSubmit(data as BeneficiaryCreatePayload);
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Prénom" error={errors.first_name?.message} required>
          <input {...register("first_name")} className={inputCls(errors.first_name?.message)} />
        </Field>
        <Field label="Nom" error={errors.last_name?.message} required>
          <input {...register("last_name")} className={inputCls(errors.last_name?.message)} />
        </Field>
        <Field label="Prénom (arabe)">
          <input {...register("first_name_ar")} className={inputCls()} dir="rtl" />
        </Field>
        <Field label="Nom (arabe)">
          <input {...register("last_name_ar")} className={inputCls()} dir="rtl" />
        </Field>
        <Field label="Genre" error={errors.gender?.message} required>
          <select {...register("gender")} className={inputCls(errors.gender?.message)}>
            <option value="">Sélectionner</option>
            <option value="M">Masculin</option>
            <option value="F">Féminin</option>
          </select>
        </Field>
        <Field label="Date de naissance" error={errors.date_of_birth?.message} required>
          <input type="date" {...register("date_of_birth")} className={inputCls(errors.date_of_birth?.message)} />
        </Field>
        <Field label="Lien de parenté" error={errors.relationship?.message} required>
          <select {...register("relationship")} className={inputCls(errors.relationship?.message)}>
            <option value="">Sélectionner</option>
            <option value="spouse">Conjoint(e)</option>
            <option value="child">Enfant</option>
            <option value="parent">Parent</option>
            <option value="sibling">Frère / Sœur</option>
            <option value="other">Autre</option>
          </select>
        </Field>
        <Field label="NNI / CIN">
          <input {...register("national_id")} className={inputCls()} />
        </Field>
      </div>

      {/* Champs spécifiques enfant */}
      {isChild && (
        <div className="p-4 bg-blue-50 rounded-xl border border-blue-200 space-y-3">
          <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Informations enfant</p>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" {...register("is_student")} className="w-4 h-4 rounded accent-brand" />
              Étudiant(e)
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" {...register("is_handicapped")} className="w-4 h-4 rounded accent-brand" />
              Handicapé(e)
            </label>
          </div>
          <Field label="Établissement scolaire">
            <input {...register("school_name")} className={inputCls()} placeholder="Nom de l'université / école" />
          </Field>
          <Field label="Année scolaire">
            <input {...register("school_year")} className={inputCls()} placeholder="2024-2025" />
          </Field>
        </div>
      )}

      {/* Champs spécifiques conjoint */}
      {isSpouse && (
        <div className="p-4 bg-purple-50 rounded-xl border border-purple-200 space-y-3">
          <p className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Informations conjoint(e)</p>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input type="checkbox" {...register("spouse_is_employed")} className="w-4 h-4 rounded accent-brand" />
            Conjoint(e) salarié(e)
          </label>
          <Field label="Employeur du/de la conjoint(e)">
            <input {...register("spouse_employer")} className={inputCls()} />
          </Field>
        </div>
      )}

      {/* Documents fournis */}
      <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-2">
        <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Documents fournis</p>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input type="checkbox" {...register("birth_certificate_uploaded")} className="w-4 h-4 rounded accent-brand" />
            Acte de naissance
          </label>
          {isSpouse && (
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" {...register("marriage_certificate_uploaded")} className="w-4 h-4 rounded accent-brand" />
              Acte de mariage
            </label>
          )}
        </div>
      </div>

      <Field label="Notes">
        <textarea {...register("notes")} rows={2} className={inputCls()} />
      </Field>

      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
          Annuler
        </button>
        <button type="submit" disabled={isLoading}
          className="flex items-center gap-2 px-5 py-2 bg-brand text-white text-sm rounded-lg hover:bg-brand-light disabled:opacity-60">
          {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
          {initialData ? "Enregistrer" : "Ajouter l'ayant droit"}
        </button>
      </div>
    </form>
  );
}
