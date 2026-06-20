import { useState } from "react";
import { useForm } from "react-hook-form";
import { useEmployees } from "@modules/employees/hooks/useEmployees";
import type { LoanCreatePayload } from "../types";

interface LoanFormProps {
  initialData?: Partial<LoanCreatePayload>;
  onSubmit: (data: LoanCreatePayload) => void;
  isLoading?: boolean;
  onCancel: () => void;
}

export function LoanForm({ initialData, onSubmit, isLoading, onCancel }: LoanFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<LoanCreatePayload>({
    defaultValues: initialData || { requested_amount: 0 } as any,
  });

  const [employeeSearch, setEmployeeSearch] = useState("");
  const [showEmployeePicker, setShowEmployeePicker] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const { data: employeesData } = useEmployees({ search: employeeSearch, page_size: 10 });

  const onSubmitForm = (data: LoanCreatePayload) => {
    if (!selectedEmployee) return;
    onSubmit({ ...data, employee: selectedEmployee.id });
  };

  return (
    <form onSubmit={handleSubmit(onSubmitForm)} className="space-y-4">
      {!selectedEmployee ? (
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Employé <span className="text-red-500">*</span></label>
          <div className="relative">
            <input type="text" placeholder="Rechercher un employé..."
              value={employeeSearch}
              onChange={(e) => { setEmployeeSearch(e.target.value); setShowEmployeePicker(true); }}
              onFocus={() => setShowEmployeePicker(true)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-brand" />
            {showEmployeePicker && employeesData?.results && (
              <div className="absolute top-full left-0 right-0 mt-1 z-50 rounded-xl overflow-hidden max-h-48 overflow-y-auto bg-white border border-gray-200 shadow-lg">
                {employeesData.results.map((emp) => (
                  <button key={emp.id} type="button"
                    onClick={() => { setSelectedEmployee(emp); setEmployeeSearch(`${emp.first_name} ${emp.last_name}`); setShowEmployeePicker(false); }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50">
                    <span className="font-medium">{emp.first_name} {emp.last_name}</span>
                    <span className="ml-2 text-xs text-gray-400">{emp.matricule}</span>
                  </button>
                ))}
                {employeesData.results.length === 0 && (
                  <p className="px-3 py-2 text-sm text-gray-400">Aucun résultat</p>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
          <div>
            <p className="text-sm font-bold">{selectedEmployee.first_name} {selectedEmployee.last_name}</p>
            <p className="text-xs text-gray-400">{selectedEmployee.matricule}</p>
          </div>
          <button type="button" onClick={() => { setSelectedEmployee(null); setEmployeeSearch(""); }}
            className="text-xs text-red-500 hover:underline">Changer</button>
        </div>
      )}

      <div>
        <label className="text-sm font-medium text-gray-700 block mb-1">Montant demandé (DZD) <span className="text-red-500">*</span></label>
        <input type="number" step="0.01" min="0"
          {...register("requested_amount", { required: "Montant requis", min: { value: 1, message: "Montant invalide" } })}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-brand" />
        {errors.requested_amount && <p className="text-xs text-red-500 mt-1">{errors.requested_amount.message}</p>}
      </div>

      <div>
        <label className="text-sm font-medium text-gray-700 block mb-1">Motif du prêt <span className="text-red-500">*</span></label>
        <textarea rows={3}
          {...register("reason", { required: "Motif requis" })}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-brand" />
        {errors.reason && <p className="text-xs text-red-500 mt-1">{errors.reason.message}</p>}
      </div>

      <div>
        <label className="text-sm font-medium text-gray-700 block mb-1">Observations</label>
        <textarea rows={2} {...register("description")}
          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl outline-none focus:border-brand" />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50">
          Annuler
        </button>
        <button type="submit" disabled={isLoading || !selectedEmployee}
          className="px-4 py-2 text-sm bg-brand text-gray-900 rounded-lg font-bold hover:bg-brand-light disabled:opacity-50">
          {isLoading ? "Création..." : "Créer le prêt"}
        </button>
      </div>
    </form>
  );
}
