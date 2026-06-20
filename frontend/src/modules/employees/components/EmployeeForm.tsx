import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, User, Building2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { clsx } from "clsx";
import { Field, inputCls } from "@shared/components/ui/index";
import { useDepartments } from "../hooks/useEmployees";
import { fetchOrganizationLookup } from "@modules/organization/api";
import type { Employee, EmployeeCreatePayload } from "../types";
import type { OrganizationLookup } from "@modules/organization/api";

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
    social_security_number: z.string().max(20).optional(),
    phone:           z.string().max(20).optional(),
    phone_secondary: z.string().max(20).optional(),
    email_personal:  z.string().email(t("validation.email")).optional().or(z.literal("")),
    email_professional: z.string().email(t("validation.email")).optional().or(z.literal("")),
    address: z.string().optional(),
    city:    z.string().max(100).optional(),
    wilaya:  z.string().max(100).optional(),
    department:    z.string().uuid().optional().or(z.literal("")),
    job_title:     z.string().max(150).optional().or(z.literal("")),
    grade:         z.string().max(100).optional(),
    grade_level:   z.coerce.number().int().min(1).max(20).optional().or(z.literal("")),
    category:      z.string().max(50).optional(),
    contract_type: z.enum(["cdi","cdd","stage","part_time","consultant"]).optional().or(z.literal("")),
    date_hired:    z.string().optional().or(z.literal("")).refine((d) => {
      if (!d) return true;
      return new Date(d) <= new Date();
    }, t("employees.validationDateFuture")),
    date_end:      z.string().optional(),
    status:        z.enum(["active","inactive","retired","suspended","deceased"]).optional(),
    base_salary:   z.coerce.number().min(0).optional().or(z.literal("")),
    bank_account:  z.string().max(50).optional(),
    education_level: z.string().max(100).optional(),
    education_field: z.string().max(100).optional(),
    notes:           z.string().optional(),
    bureau:          z.string().optional().or(z.literal("")),
    function:        z.string().optional().or(z.literal("")),
    grade_ref:       z.string().optional().or(z.literal("")),
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

type TabId = "identity" | "org";

export function EmployeeForm({
  initialData, onSubmit, onCancel, isLoading, mode = "create",
}: EmployeeFormProps) {
  const { t } = useTranslation();
  const TABS = [
    { id: "identity" as TabId, label: t("employees.identity"), icon: User },
    { id: "org" as TabId, label: t("employees.assignment"), icon: Building2 },
  ];
  const [activeTab, setActiveTab] = useState<TabId>("identity");
  const { data: deptData } = useDepartments({ is_active: true });
  const departments = deptData?.results ?? [];

  const [orgLookup, setOrgLookup] = useState<OrganizationLookup | null>(null);
  const [orgLoading, setOrgLoading] = useState(true);
  const [orgError, setOrgError] = useState<string | null>(null);
  const [selectedDirection, setSelectedDirection] = useState<string | "">("");
  const [selectedSubDirection, setSelectedSubDirection] = useState<string | "">("");
  const [selectedService, setSelectedService] = useState<string | "">("");

  const employeeSchema = createEmployeeSchema(t);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    setValue,
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
          social_security_number: initialData.social_security_number ?? "",
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
          bureau:          initialData.bureau ?? "",
          function:        initialData.function ?? "",
          grade_ref:       initialData.grade_ref ?? "",
        }
      : { contract_type: "cdi", status: "active", nationality: t("employees.nationalityDefault"), marital_status: "single" },
  });

  useEffect(() => {
    setOrgLoading(true);
    setOrgError(null);
    fetchOrganizationLookup()
      .then(setOrgLookup)
      .catch(() => setOrgError(t("employees.loadOrgError")))
      .finally(() => setOrgLoading(false));
  }, []);

  useEffect(() => {
    if (!initialData || !orgLookup) return;
    const bureau = orgLookup.bureaux.find(b => b.id === initialData.bureau);
    if (bureau) {
      setSelectedService(bureau.service);
      const service = orgLookup.services.find(s => s.id === bureau.service);
      if (service) {
        setSelectedSubDirection(service.sub_direction);
        const sd = orgLookup.sub_directions.find(s => s.id === service.sub_direction);
        if (sd) setSelectedDirection(sd.direction);
      }
    }
  }, [initialData, orgLookup]);

  const handleFormSubmit = handleSubmit(async (data) => {
    const cleaned = Object.fromEntries(
      Object.entries(data).filter(([, v]) => v !== "" && v != null)
    ) as unknown as EmployeeCreatePayload;
    await onSubmit(cleaned);
  });

  const tabErrors: Record<TabId, number> = {
    identity: ["first_name","last_name","gender","date_of_birth","phone","email_professional"].filter(f => errors[f as keyof FormData]).length,
    org:      0,
  };

  const directions = orgLookup?.directions ?? [];
  const subDirections = (orgLookup?.sub_directions ?? []).filter(sd => sd.direction === selectedDirection);
  const services = (orgLookup?.services ?? []).filter(s => s.sub_direction === selectedSubDirection);
  const bureaux = (orgLookup?.bureaux ?? []).filter(b => b.service === selectedService);
  const functions = orgLookup?.functions ?? [];
  const grades = orgLookup?.grades ?? [];

  return (
    <form onSubmit={handleFormSubmit} className="space-y-0">
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

      {activeTab === "identity" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={t("employees.firstName")} error={errors.first_name?.message} required>
            <input {...register("first_name")} className={inputCls(errors.first_name?.message)} placeholder={t("employees.placeholderFirstName")} />
          </Field>
          <Field label={t("employees.lastName")} error={errors.last_name?.message} required>
            <input {...register("last_name")} className={inputCls(errors.last_name?.message)} placeholder={t("employees.placeholderLastName")} />
          </Field>
          <Field label={t("employees.firstNameArabic")} error={errors.first_name_ar?.message}>
            <input {...register("first_name_ar")} className={inputCls()} dir="rtl" placeholder={t("employees.firstNameArPlaceholder")} />
          </Field>
          <Field label={t("employees.lastNameArabic")} error={errors.last_name_ar?.message}>
            <input {...register("last_name_ar")} className={inputCls()} dir="rtl" placeholder={t("employees.lastNameArPlaceholder")} />
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
            <input {...register("social_security_number")} className={inputCls()} />
          </Field>
          <Field label={t("employees.nationalityLabel")}>
            <input {...register("nationality")} className={inputCls()} defaultValue={t("employees.nationalityDefault")} />
          </Field>
          <div className="md:col-span-2 border-t border-gray-100 my-2" />
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

      {activeTab === "org" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orgLoading ? (
            <div className="md:col-span-2 flex items-center justify-center py-12 text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              {t("common.loading")}
            </div>
          ) : orgError ? (
            <div className="md:col-span-2 bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
              {orgError}
            </div>
          ) : (<>
          <Field label={t("employees.department")} error={errors.department?.message}>
            <select {...register("department")} className={inputCls(errors.department?.message)}>
              <option value="">{t("employees.selectDepartment")}</option>
              {departments.map((d: any) => (
                <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
              ))}
            </select>
          </Field>
          <Field label={t("employees.jobTitle")} error={errors.job_title?.message}>
            <input {...register("job_title")} className={inputCls(errors.job_title?.message)} placeholder={t("employees.placeholderJobTitle")} />
          </Field>

          <div className="md:col-span-2 border-t border-gray-100 my-2" />

          <Field label={t("employees.direction")}>
            <select
              className={inputCls()}
              value={selectedDirection}
              onChange={(e) => {
                setSelectedDirection(e.target.value);
                setSelectedSubDirection("");
                setSelectedService("");
                setValue("bureau", "");
              }}
            >
              <option value="">{t("employees.selectDirection")}</option>
              {directions.map((d) => (
                <option key={d.id} value={d.id}>{d.code} — {d.name}</option>
              ))}
            </select>
          </Field>
          <Field label={t("employees.subDirection")}>
            <select
              className={inputCls()}
              value={selectedSubDirection}
              onChange={(e) => {
                setSelectedSubDirection(e.target.value);
                setSelectedService("");
                setValue("bureau", "");
              }}
              disabled={!selectedDirection}
            >
              <option value="">{t("employees.selectSubDirection")}</option>
              {subDirections.map((sd) => (
                <option key={sd.id} value={sd.id}>{sd.code} — {sd.name}</option>
              ))}
            </select>
          </Field>
          <Field label={t("employees.service")}>
            <select
              className={inputCls()}
              value={selectedService}
              onChange={(e) => {
                setSelectedService(e.target.value);
                setValue("bureau", "");
              }}
              disabled={!selectedSubDirection}
            >
              <option value="">{t("employees.selectService")}</option>
              {services.map((s) => (
                <option key={s.id} value={s.id}>{s.code} — {s.name}</option>
              ))}
            </select>
          </Field>
          <Field label={t("employees.bureau")} error={errors.bureau?.message}>
            <select
              {...register("bureau")}
              className={inputCls(errors.bureau?.message)}
              disabled={!selectedService}
            >
              <option value="">{t("employees.selectBureau")}</option>
              {bureaux.map((b) => (
                <option key={b.id} value={b.id}>{b.code} — {b.name}</option>
              ))}
            </select>
          </Field>

          <div className="md:col-span-2 border-t border-gray-100 my-2" />

          <Field label={t("employees.function")}>
            <select {...register("function")} className={inputCls()}>
              <option value="">{t("employees.selectFunction")}</option>
              {functions.map((f) => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </Field>
          <Field label={t("employees.gradeRef")}>
            <select {...register("grade_ref")} className={inputCls()}>
              <option value="">{t("employees.selectGrade")}</option>
              {grades.map((g) => (
                <option key={g.id} value={g.id}>{g.name} (Niv. {g.level})</option>
              ))}
            </select>
          </Field>

          <div className="md:col-span-2 border-t border-gray-100 my-2" />

          <Field label={t("employees.grade")}>
            <input {...register("grade")} className={inputCls()} placeholder={t("employees.placeholderGrade")} />
          </Field>
          <Field label={t("employees.gradeLevel")} hint={t("employees.gradeLevelHint")}>
            <input type="number" {...register("grade_level")} className={inputCls()} min={1} max={20} />
          </Field>
          <Field label={t("employees.category")}>
            <input {...register("category")} className={inputCls()} placeholder={t("employees.placeholderCategory")} />
          </Field>
          <Field label={t("employees.contractType")} error={errors.contract_type?.message}>
            <select {...register("contract_type")} className={inputCls(errors.contract_type?.message)}>
              <option value="cdi">{t("employees.cdi")}</option>
              <option value="cdd">{t("employees.cdd")}</option>
              <option value="stage">{t("employees.intern")}</option>
              <option value="part_time">{t("employees.noContractType")}</option>
              <option value="consultant">{t("employees.consultant")}</option>
            </select>
          </Field>
          <Field label={t("employees.dateHired")} error={errors.date_hired?.message}>
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

          <div className="md:col-span-2 border-t border-gray-100 my-2" />

          <Field label={t("employees.educationLevel")}>
            <input {...register("education_level")} className={inputCls()} placeholder={t("employees.placeholderEducationLevel")} />
          </Field>
          <Field label={t("employees.educationField")}>
            <input {...register("education_field")} className={inputCls()} placeholder={t("employees.placeholderEducationField")} />
          </Field>
          <Field label={t("employees.internalNotes")} className="md:col-span-2">
            <textarea {...register("notes")} rows={4} className={inputCls()} placeholder={t("employees.placeholderNotes")} />
          </Field>
            </>)}
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
