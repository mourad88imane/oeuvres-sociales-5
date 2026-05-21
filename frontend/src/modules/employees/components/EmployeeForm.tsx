/**
 * EMPLOYEE FORM — Formulaire création / modification
 * Validation Zod + React Hook Form
 * Tabs : Identité | Contact | Poste | Complément
 */
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, User, Phone, Briefcase, GraduationCap } from "lucide-react";
import { clsx } from "clsx";
import { Field, inputCls } from "@shared/components/ui/index";
import { useDepartments } from "../hooks/useEmployees";
import type { Employee, EmployeeCreatePayload } from "../types";

// ── Schéma de validation Zod ───────────────────────────────
const employeeSchema = z.object({
  first_name:    z.string().min(2, "Minimum 2 caractères").max(100),
  last_name:     z.string().min(2, "Minimum 2 caractères").max(100),
  first_name_ar: z.string().max(100).optional(),
  last_name_ar:  z.string().max(100).optional(),
  gender:        z.enum(["M", "F"], { required_error: "Champ obligatoire" }),
  date_of_birth: z.string().min(1, "Champ obligatoire").refine((d) => {
    const age = (Date.now() - new Date(d).getTime()) / (1000 * 60 * 60 * 24 * 365.25);
    return age >= 16 && age <= 100;
  }, "Âge doit être entre 16 et 100 ans"),
  place_of_birth:  z.string().max(100).optional(),
  marital_status:  z.enum(["single","married","divorced","widowed"]).optional(),
  nationality:     z.string().max(50).optional(),
  national_id:     z.string().max(20).optional(),
  national_id_expiry: z.string().optional(),
  phone:           z.string().max(20).optional(),
  phone_secondary: z.string().max(20).optional(),
  email_personal:  z.string().email("Email invalide").optional().or(z.literal("")),
  email_professional: z.string().email("Email invalide").optional().or(z.literal("")),
  address: z.string().optional(),
  city:    z.string().max(100).optional(),
  wilaya:  z.string().max(100).optional(),
  department:    z.string().uuid("Département requis"),
  job_title:     z.string().min(2, "Champ obligatoire").max(150),
  grade:         z.string().max(100).optional(),
  grade_level:   z.coerce.number().int().min(1).max(20).optional().or(z.literal("")),
  category:      z.string().max(50).optional(),
  contract_type: z.enum(["cdi","cdd","stage","part_time","consultant"]),
  date_hired:    z.string().min(1, "Champ obligatoire").refine((d) => {
    return new Date(d) <= new Date();
  }, "La date d'embauche ne peut pas être dans le futur"),
  date_end:      z.string().optional(),
  status:        z.enum(["active","inactive","retired","suspended","deceased"]).optional(),
  base_salary:   z.coerce.number().min(0).optional().or(z.literal("")),
  bank_account:  z.string().max(50).optional(),
  education_level: z.string().max(100).optional(),
  education_field: z.string().max(100).optional(),
  notes:           z.string().optional(),
});

type FormData = z.infer<typeof employeeSchema>;

interface EmployeeFormProps {
  initialData?: Employee;
  onSubmit: (data: EmployeeCreatePayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  mode?: "create" | "edit";
}

// ── Onglets du formulaire ──────────────────────────────────
const TABS = [
  { id: "identity", label: "Identité",  icon: User },
  { id: "contact",  label: "Contact",   icon: Phone },
  { id: "job",      label: "Poste",     icon: Briefcase },
  { id: "extra",    label: "Complément",icon: GraduationCap },
] as const;

type TabId = typeof TABS[number]["id"];

export function EmployeeForm({
  initialData, onSubmit, onCancel, isLoading, mode = "create",
}: EmployeeFormProps) {
  const [activeTab, setActiveTab] = useState<TabId>("identity");
  const { data: deptData } = useDepartments({ is_active: true });
  const departments = deptData?.results ?? [];

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(employeeSchema),
    defaultValues: initialData
      ? {
          first_name: initialData.first_name,
          last_name:  initialData.last_name,
          first_name_ar: initialData.first_name_ar,
          last_name_ar:  initialData.last_name_ar,
          gender:        initialData.gender,
          date_of_birth: initialData.date_of_birth,
          place_of_birth: initialData.place_of_birth,
          marital_status: initialData.marital_status,
          nationality:    initialData.nationality,
          national_id:    initialData.national_id,
          national_id_expiry: initialData.national_id_expiry ?? "",
          phone:           initialData.phone,
          phone_secondary: initialData.phone_secondary,
          email_personal:  initialData.email_personal,
          email_professional: initialData.email_professional,
          address: initialData.address,
          city:    initialData.city,
          wilaya:  initialData.wilaya,
          department:    initialData.department,
          job_title:     initialData.job_title,
          grade:         initialData.grade,
          grade_level:   initialData.grade_level ?? "",
          category:      initialData.category,
          contract_type: initialData.contract_type,
          date_hired:    initialData.date_hired,
          date_end:      initialData.date_end ?? "",
          status:        initialData.status,
          base_salary:   initialData.base_salary ?? "",
          bank_account:  initialData.bank_account,
          education_level: initialData.education_level,
          education_field: initialData.education_field,
          notes:           initialData.notes,
        }
      : { contract_type: "cdi", status: "active", nationality: "Algérienne", marital_status: "single" },
  });

  const handleFormSubmit = handleSubmit(async (data) => {
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v != null)
    ) as unknown as EmployeeCreatePayload;
    await onSubmit(cleaned);
  });

  // Compte les erreurs par onglet pour l'indicateur
  const tabErrors: Record<TabId, number> = {
    identity: ["first_name","last_name","gender","date_of_birth","national_id"].filter(f => errors[f as keyof FormData]).length,
    contact:  ["phone","email_personal","email_professional","address"].filter(f => errors[f as keyof FormData]).length,
    job:      ["department","job_title","contract_type","date_hired"].filter(f => errors[f as keyof FormData]).length,
    extra:    ["education_level","notes"].filter(f => errors[f as keyof FormData]).length,
  };

  return (
    <form onSubmit={handleFormSubmit} className="space-y-0">
      {/* ── Onglets ──────────────────────────────────── */}
      <div className="flex gap-1 border-b border-gray-200 mb-5">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id} type="button" onClick={() => setActiveTab(id)}
            className={clsx(
              "flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors relative",
              activeTab === id
                ? "text-brand border-b-2 border-brand -mb-px bg-blue-50"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-50",
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
            {tabErrors[id] > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {tabErrors[id]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════
          TAB : IDENTITÉ
      ════════════════════════════════════════════════ */}
      {activeTab === "identity" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Prénom" error={errors.first_name?.message} required>
            <input {...register("first_name")} className={inputCls(errors.first_name?.message)} placeholder="Prénom en français" />
          </Field>
          <Field label="Nom" error={errors.last_name?.message} required>
            <input {...register("last_name")} className={inputCls(errors.last_name?.message)} placeholder="Nom en français" />
          </Field>
          <Field label="Prénom (arabe)" error={errors.first_name_ar?.message}>
            <input {...register("first_name_ar")} className={inputCls()} dir="rtl" placeholder="الاسم الأول" />
          </Field>
          <Field label="Nom (arabe)" error={errors.last_name_ar?.message}>
            <input {...register("last_name_ar")} className={inputCls()} dir="rtl" placeholder="اللقب" />
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
          <Field label="Lieu de naissance">
            <input {...register("place_of_birth")} className={inputCls()} placeholder="Wilaya / Commune" />
          </Field>
          <Field label="Situation familiale">
            <select {...register("marital_status")} className={inputCls()}>
              <option value="single">Célibataire</option>
              <option value="married">Marié(e)</option>
              <option value="divorced">Divorcé(e)</option>
              <option value="widowed">Veuf/Veuve</option>
            </select>
          </Field>
          <Field label="NNI / CIN" hint="Numéro national d'identité">
            <input {...register("national_id")} className={inputCls()} placeholder="XXXXXXXXXXXXXXXX" />
          </Field>
          <Field label="Expiration CIN">
            <input type="date" {...register("national_id_expiry")} className={inputCls()} />
          </Field>
          <Field label="N° Sécurité Sociale">
            <input {...register("social_security_number" as keyof FormData)} className={inputCls()} />
          </Field>
          <Field label="Nationalité">
            <input {...register("nationality")} className={inputCls()} defaultValue="Algérienne" />
          </Field>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : CONTACT
      ════════════════════════════════════════════════ */}
      {activeTab === "contact" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Téléphone principal" error={errors.phone?.message}>
            <input {...register("phone")} className={inputCls()} placeholder="+213 XXX XXX XXX" />
          </Field>
          <Field label="Téléphone secondaire">
            <input {...register("phone_secondary")} className={inputCls()} placeholder="+213 XXX XXX XXX" />
          </Field>
          <Field label="Email personnel" error={errors.email_personal?.message}>
            <input type="email" {...register("email_personal")} className={inputCls(errors.email_personal?.message)} />
          </Field>
          <Field label="Email professionnel" error={errors.email_professional?.message}>
            <input type="email" {...register("email_professional")} className={inputCls(errors.email_professional?.message)} />
          </Field>
          <Field label="Adresse" className="md:col-span-2">
            <textarea {...register("address")} rows={2} className={inputCls()} placeholder="Numéro, rue, quartier..." />
          </Field>
          <Field label="Ville">
            <input {...register("city")} className={inputCls()} />
          </Field>
          <Field label="Wilaya">
            <input {...register("wilaya")} className={inputCls()} placeholder="Alger, Oran, Constantine..." />
          </Field>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : POSTE
      ════════════════════════════════════════════════ */}
      {activeTab === "job" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Département" error={errors.department?.message} required>
            <select {...register("department")} className={inputCls(errors.department?.message)}>
              <option value="">Sélectionner un département</option>
              {departments.map((d: any) => (
                <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
              ))}
            </select>
          </Field>
          <Field label="Intitulé du poste" error={errors.job_title?.message} required>
            <input {...register("job_title")} className={inputCls(errors.job_title?.message)} placeholder="Ex : Ingénieur Développement" />
          </Field>
          <Field label="Grade / Échelon">
            <input {...register("grade")} className={inputCls()} placeholder="Ex : Grade A, Échelon 3" />
          </Field>
          <Field label="Niveau de grade" hint="Valeur numérique (1-20) pour comparaisons">
            <input type="number" {...register("grade_level")} className={inputCls()} min={1} max={20} />
          </Field>
          <Field label="Catégorie socio-professionnelle">
            <input {...register("category")} className={inputCls()} placeholder="Cadre, Technicien, Agent..." />
          </Field>
          <Field label="Type de contrat" error={errors.contract_type?.message} required>
            <select {...register("contract_type")} className={inputCls(errors.contract_type?.message)}>
              <option value="cdi">CDI</option>
              <option value="cdd">CDD</option>
              <option value="stage">Stagiaire</option>
              <option value="part_time">Temps partiel</option>
              <option value="consultant">Consultant</option>
            </select>
          </Field>
          <Field label="Date d'embauche" error={errors.date_hired?.message} required>
            <input type="date" {...register("date_hired")} className={inputCls(errors.date_hired?.message)} />
          </Field>
          <Field label="Date de fin de contrat" hint="Remplir pour les CDD">
            <input type="date" {...register("date_end")} className={inputCls()} />
          </Field>
          <Field label="Statut">
            <select {...register("status")} className={inputCls()}>
              <option value="active">Actif</option>
              <option value="inactive">Inactif</option>
              <option value="retired">Retraité</option>
              <option value="suspended">Suspendu</option>
            </select>
          </Field>
          <Field label="Salaire de base (DZD)">
            <input type="number" {...register("base_salary")} className={inputCls()} min={0} step={500} />
          </Field>
          <Field label="RIB / CCP">
            <input {...register("bank_account")} className={inputCls()} placeholder="CCP ou RIB bancaire" />
          </Field>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : COMPLÉMENT
      ════════════════════════════════════════════════ */}
      {activeTab === "extra" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Niveau de formation">
            <input {...register("education_level")} className={inputCls()} placeholder="Bac+5, Ingénieur, Master..." />
          </Field>
          <Field label="Domaine de formation">
            <input {...register("education_field")} className={inputCls()} placeholder="Informatique, Gestion, Droit..." />
          </Field>
          <Field label="Notes internes" className="md:col-span-2">
            <textarea {...register("notes")} rows={4} className={inputCls()} placeholder="Informations complémentaires..." />
          </Field>
        </div>
      )}

      {/* ── Navigation onglets + Boutons ─────────────── */}
      <div className="flex items-center justify-between pt-5 mt-5 border-t border-gray-200">
        <div className="flex gap-2">
          {TABS.map(({ id }) => (
            <button
              key={id} type="button" onClick={() => setActiveTab(id)}
              className={clsx(
                "w-2.5 h-2.5 rounded-full transition-colors",
                activeTab === id ? "bg-brand" : "bg-gray-300 hover:bg-gray-400",
              )}
            />
          ))}
        </div>
        <div className="flex gap-3">
          <button type="button" onClick={onCancel}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
            Annuler
          </button>
          <button
            type="submit"
            disabled={isLoading || (mode === "edit" && !isDirty)}
            className="flex items-center gap-2 px-5 py-2 bg-brand text-white text-sm rounded-lg
              hover:bg-brand-light transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {mode === "create" ? "Créer l'employé" : "Enregistrer les modifications"}
          </button>
        </div>
      </div>
    </form>
  );
}
