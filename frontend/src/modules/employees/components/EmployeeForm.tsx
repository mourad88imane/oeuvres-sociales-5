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
import { useTranslation } from "react-i18next";
import { clsx } from "clsx";
import { Field, inputCls } from "@shared/components/ui/index";
import { useDepartments } from "../hooks/useEmployees";
import type { Employee, EmployeeCreatePayload } from "../types";

function createEmployeeSchema(t: (key: string, opts?: Record<string, unknown>) => string) {
  return z.object({
    first_name:    z.string().min(2, t("validation.minLength", { count: 2 })).max(100),
    last_name:     z.string().min(2, t("validation.minLength", { count: 2 })).max(100),
    first_name_ar: z.string().max(100).optional(),
    last_name_ar:  z.string().max(100).optional(),
    gender:        z.enum(["M", "F"], { required_error: t("validation.required") }),
    date_of_birth: z.string().min(1, t("validation.required")).refine((d) => {
      const age = (Date.now() - new Date(d).getTime()) / (1000 * 60 * 60 * 24 * 365.25);
      return age >= 16 && age <= 100;
    }, t("employees.validationAgeRange")),
    place_of_birth:  z.string().max(100).optional(),
    marital_status:  z.enum(["single","married","divorced","widowed"]).optional(),
    nationality:     z.string().max(50).optional(),
    national_id:     z.string().max(20).optional(),
    national_id_expiry: z.string().optional(),
    phone:           z.string().max(20).optional(),
    phone_secondary: z.string().max(20).optional(),
    email_personal:  z.string().email(t("validation.email")).optional().or(z.literal("")),
    email_professional: z.string().email(t("validation.email")).optional().or(z.literal("")),
    address: z.string().optional(),
    city:    z.string().max(100).optional(),
    wilaya:  z.string().max(100).optional(),
    department:    z.string().uuid(t("employees.validationDepartmentRequired")),
    job_title:     z.string().min(2, t("validation.required")).max(150),
    grade:         z.string().max(100).optional(),
    grade_level:   z.coerce.number().int().min(1).max(20).optional().or(z.literal("")),
    category:      z.string().max(50).optional(),
    contract_type: z.enum(["cdi","cdd","stage","part_time","consultant"]),
    date_hired:    z.string().min(1, t("validation.required")).refine((d) => {
      return new Date(d) <= new Date();
    }, t("employees.validationDateFuture")),
    date_end:      z.string().optional(),
    status:        z.enum(["active","inactive","retired","suspended","deceased"]).optional(),
    base_salary:   z.coerce.number().min(0).optional().or(z.literal("")),
    bank_account:  z.string().max(50).optional(),
    education_level: z.string().max(100).optional(),
    education_field: z.string().max(100).optional(),
    notes:           z.string().optional(),
  });
}

type FormData = z.infer<ReturnType<typeof createEmployeeSchema>>;

interface EmployeeFormProps {
  initialData?: Employee;
  onSubmit: (data: EmployeeCreatePayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  mode?: "create" | "edit";
}

type TabId = "identity" | "contact" | "job" | "extra";

export function EmployeeForm({
  initialData, onSubmit, onCancel, isLoading, mode = "create",
}: EmployeeFormProps) {
  const { t } = useTranslation();
  const TABS = [
    { id: "identity" as TabId, label: t("employees.identity"),    icon: User },
    { id: "contact"  as TabId, label: t("employees.contacts"),    icon: Phone },
    { id: "job"      as TabId, label: t("employees.position"),    icon: Briefcase },
    { id: "extra"    as TabId, label: t("employees.extra"),       icon: GraduationCap },
  ];
  const [activeTab, setActiveTab] = useState<TabId>("identity");
  const { data: deptData } = useDepartments({ is_active: true });
  const departments = deptData?.results ?? [];
  const employeeSchema = createEmployeeSchema(t);

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
          <Field label={t("employees.firstName")} error={errors.first_name?.message} required>
            <input {...register("first_name")} className={inputCls(errors.first_name?.message)} placeholder={t("employees.placeholderFirstName")} />
          </Field>
          <Field label={t("employees.lastName")} error={errors.last_name?.message} required>
            <input {...register("last_name")} className={inputCls(errors.last_name?.message)} placeholder={t("employees.placeholderLastName")} />
          </Field>
          <Field label={t("employees.firstNameArabic")} error={errors.first_name_ar?.message}>
            <input {...register("first_name_ar")} className={inputCls()} dir="rtl" placeholder="الاسم الأول" />
          </Field>
          <Field label={t("employees.lastNameArabic")} error={errors.last_name_ar?.message}>
            <input {...register("last_name_ar")} className={inputCls()} dir="rtl" placeholder="اللقب" />
          </Field>
          <Field label={t("employees.gender")} error={errors.gender?.message} required>
            <select {...register("gender")} className={inputCls(errors.gender?.message)}>
              <option value="">{t("common.selectOption")}</option>
              <option value="M">{t("employees.male")}</option>
              <option value="F">{t("employees.female")}</option>
            </select>
          </Field>
          <Field label={t("employees.dateOfBirth")} error={errors.date_of_birth?.message} required>
            <input type="date" {...register("date_of_birth")} className={inputCls(errors.date_of_birth?.message)} />
          </Field>
          <Field label={t("employees.placeOfBirth")}>
            <input {...register("place_of_birth")} className={inputCls()} placeholder={t("employees.placeholderPlaceOfBirth")} />
          </Field>
          <Field label={t("employees.maritalStatus")}>
            <select {...register("marital_status")} className={inputCls()}>
              <option value="single">{t("employees.single")}</option>
              <option value="married">{t("employees.married")}</option>
              <option value="divorced">{t("employees.divorced")}</option>
              <option value="widowed">{t("employees.widowed")}</option>
            </select>
          </Field>
          <Field label={t("employees.nationalId")}>
            <input {...register("national_id")} className={inputCls()} placeholder={t("employees.placeholderNationalId")} />
          </Field>
          <Field label={t("employees.cinExpiry")}>
            <input type="date" {...register("national_id_expiry")} className={inputCls()} />
          </Field>
          <Field label={t("employees.socialSecurityNumber")}>
            <input {...register("social_security_number" as keyof FormData)} className={inputCls()} />
          </Field>
          <Field label={t("employees.nationalityLabel")}>
            <input {...register("nationality")} className={inputCls()} defaultValue="Algérienne" />
          </Field>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : CONTACT
      ════════════════════════════════════════════════ */}
      {activeTab === "contact" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={t("employees.phone")} error={errors.phone?.message}>
            <input {...register("phone")} className={inputCls()} placeholder={t("employees.placeholderPhone")} />
          </Field>
          <Field label={t("employees.phoneSecondary")}>
            <input {...register("phone_secondary")} className={inputCls()} placeholder={t("employees.placeholderPhone")} />
          </Field>
          <Field label={t("employees.emailPersonal")} error={errors.email_personal?.message}>
            <input type="email" {...register("email_personal")} className={inputCls(errors.email_personal?.message)} />
          </Field>
          <Field label={t("employees.email")} error={errors.email_professional?.message}>
            <input type="email" {...register("email_professional")} className={inputCls(errors.email_professional?.message)} />
          </Field>
          <Field label={t("employees.address")} className="md:col-span-2">
            <textarea {...register("address")} rows={2} className={inputCls()} placeholder={t("employees.placeholderAddress")} />
          </Field>
          <Field label={t("common.city")}>
            <input {...register("city")} className={inputCls()} />
          </Field>
          <Field label={t("employees.wilaya")}>
            <input {...register("wilaya")} className={inputCls()} placeholder={t("employees.placeholderWilaya")} />
          </Field>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : POSTE
      ════════════════════════════════════════════════ */}
      {activeTab === "job" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={t("employees.department")} error={errors.department?.message} required>
            <select {...register("department")} className={inputCls(errors.department?.message)}>
              <option value="">{t("employees.selectDepartment")}</option>
              {departments.map((d: any) => (
                <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
              ))}
            </select>
          </Field>
          <Field label={t("employees.jobTitle")} error={errors.job_title?.message} required>
            <input {...register("job_title")} className={inputCls(errors.job_title?.message)} placeholder={t("employees.placeholderJobTitle")} />
          </Field>
          <Field label={t("employees.grade")}>
            <input {...register("grade")} className={inputCls()} placeholder={t("employees.placeholderGrade")} />
          </Field>
          <Field label={t("employees.gradeLevel")} hint={t("employees.gradeLevelHint")}>
            <input type="number" {...register("grade_level")} className={inputCls()} min={1} max={20} />
          </Field>
          <Field label={t("employees.category")}>
            <input {...register("category")} className={inputCls()} placeholder={t("employees.placeholderCategory")} />
          </Field>
          <Field label={t("employees.contractType")} error={errors.contract_type?.message} required>
            <select {...register("contract_type")} className={inputCls(errors.contract_type?.message)}>
              <option value="cdi">{t("employees.cdi")}</option>
              <option value="cdd">{t("employees.cdd")}</option>
              <option value="stage">{t("employees.intern")}</option>
              <option value="part_time">{t("employees.noContractType")}</option>
              <option value="consultant">{t("employees.consultant")}</option>
            </select>
          </Field>
          <Field label={t("employees.dateHired")} error={errors.date_hired?.message} required>
            <input type="date" {...register("date_hired")} className={inputCls(errors.date_hired?.message)} />
          </Field>
          <Field label={t("employees.contractEnd")} hint={t("employees.contractEndHint")}>
            <input type="date" {...register("date_end")} className={inputCls()} />
          </Field>
          <Field label={t("employees.status")}>
            <select {...register("status")} className={inputCls()}>
              <option value="active">{t("employees.active")}</option>
              <option value="inactive">{t("employees.inactive")}</option>
              <option value="retired">{t("employees.retired")}</option>
              <option value="suspended">{t("employees.suspended")}</option>
            </select>
          </Field>
          <Field label={t("employees.salary")}>
            <input type="number" {...register("base_salary")} className={inputCls()} min={0} step={500} />
          </Field>
          <Field label={t("common.bankAccount")}>
            <input {...register("bank_account")} className={inputCls()} placeholder={t("employees.placeholderBankAccount")} />
          </Field>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          TAB : COMPLÉMENT
      ════════════════════════════════════════════════ */}
      {activeTab === "extra" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={t("employees.educationLevel")}>
            <input {...register("education_level")} className={inputCls()} placeholder={t("employees.placeholderEducationLevel")} />
          </Field>
          <Field label={t("employees.educationField")}>
            <input {...register("education_field")} className={inputCls()} placeholder={t("employees.placeholderEducationField")} />
          </Field>
          <Field label={t("employees.internalNotes")} className="md:col-span-2">
            <textarea {...register("notes")} rows={4} className={inputCls()} placeholder={t("employees.placeholderNotes")} />
          </Field>
        </div>
      )}

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
            {t("common.cancel")}
          </button>
          <button
            type="submit"
            disabled={isLoading || (mode === "edit" && !isDirty)}
            className="flex items-center gap-2 px-5 py-2 bg-brand text-white text-sm rounded-lg
              hover:bg-brand-light transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {mode === "create" ? t("employees.createEmployee") : t("employees.saveChanges")}
          </button>
        </div>
      </div>
    </form>
  );
}
