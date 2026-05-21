import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateConvention, usePartners } from "../api/index";
import { Field, inputCls, Spinner } from "@shared/components/ui/index";

const schema = z.object({
  partner: z.string().min(1, "Partenaire obligatoire"),
  title: z.string().min(3, "Titre obligatoire (min 3 car.)"),
  description: z.string().optional(),
  renewal_mode: z.enum(["auto", "manual", "none"]),
  renewal_notice_days: z.coerce.number().min(0).default(30),
  start_date: z.string().min(1, "Date d'effet obligatoire"),
  end_date: z.string().min(1, "Date d'échéance obligatoire"),
  signed_date: z.string().optional(),
  amount: z.coerce.number().positive().optional().or(z.literal("")),
  auto_renewal_days: z.coerce.number().min(0).default(0),
  requires_attachments: z.boolean().default(false),
});

type FormData = z.infer<typeof schema>;

export function ConventionCreatePage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const createMut = useCreateConvention();
  const { data: partnersData } = usePartners({ is_active: "true", page_size: "200" });

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { renewal_mode: "manual", renewal_notice_days: 30, auto_renewal_days: 0, requires_attachments: false },
  });

  const partners = partnersData?.results ?? [];

  const onSubmit = handleSubmit(async (data) => {
    setServerError("");
    const payload = { ...data, amount: data.amount ? Number(data.amount) : null };
    try {
      await createMut.mutateAsync(payload as never);
      navigate("/conventions");
    } catch (err: unknown) {
      const resp = err as { response?: { data?: { detail?: string } } };
      setServerError(resp?.response?.data?.detail ?? "Erreur lors de la création");
    }
  });

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <button onClick={() => navigate("/conventions")}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4" />Retour
      </button>

      <div className="card p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-6">Nouvelle convention</h1>

        {serverError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {serverError}
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-5">
          <Field label="Partenaire" error={errors.partner?.message} required>
            <select {...register("partner")} className={inputCls(errors.partner?.message)}>
              <option value="">Sélectionner un partenaire</option>
              {partners.map(p => (
                <option key={p.id} value={p.id}>[{p.code}] {p.name}</option>
              ))}
            </select>
          </Field>

          <Field label="Objet de la convention" error={errors.title?.message} required>
            <input {...register("title")} className={inputCls(errors.title?.message)}
              placeholder="Ex: Convention de partenariat médical" />
          </Field>

          <Field label="Description">
            <textarea {...register("description")} rows={3} className={inputCls()}
              placeholder="Description optionnelle..." />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Date d'effet" error={errors.start_date?.message} required>
              <input type="date" {...register("start_date")} className={inputCls(errors.start_date?.message)} />
            </Field>
            <Field label="Date d'échéance" error={errors.end_date?.message} required>
              <input type="date" {...register("end_date")} className={inputCls(errors.end_date?.message)} />
            </Field>
            <Field label="Date de signature">
              <input type="date" {...register("signed_date")} className={inputCls()} />
            </Field>
            <Field label="Montant (DZD)">
              <input type="number" step="0.01" min="0" {...register("amount")}
                className={inputCls(errors.amount?.message)} placeholder="Optionnel" />
            </Field>
          </div>

          <div className="border-t border-gray-200 pt-4">
            <p className="text-xs font-semibold text-gray-500 mb-3">Reconduction</p>
            <div className="grid grid-cols-3 gap-4">
              <Field label="Mode de reconduction" error={errors.renewal_mode?.message}>
                <select {...register("renewal_mode")} className={inputCls(errors.renewal_mode?.message)}>
                  <option value="auto">Reconduction tacite</option>
                  <option value="manual">Reconduction expresse</option>
                  <option value="none">Non reconductible</option>
                </select>
              </Field>
              <Field label="Préavis (jours)">
                <input type="number" min="0" {...register("renewal_notice_days")}
                  className={inputCls()} />
              </Field>
              <Field label="Reconduction auto (jours)">
                <input type="number" min="0" {...register("auto_renewal_days")}
                  className={inputCls()} />
              </Field>
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input type="checkbox" {...register("requires_attachments")}
              className="w-4 h-4 rounded accent-brand" />
            Pièces jointes obligatoires
          </label>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button type="button" onClick={() => navigate("/conventions")}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
              Annuler
            </button>
            <button type="submit" disabled={createMut.isPending}
              className="flex items-center gap-2 px-5 py-2 bg-brand text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-60">
              {createMut.isPending ? <Spinner size="sm" /> : <Save className="w-4 h-4" />}
              Créer la convention
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
