import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Tabs, Form, Input, InputNumber, Button, Card, message, Select, Alert } from "antd";
import { ArrowLeft, Save, User, FileText, CheckCircle, AlertTriangle } from "lucide-react";
import { useEmployees } from "@modules/employees/hooks/useEmployees";
import { useCreateLoan } from "../hooks/useLoans";

const { TextArea } = Input;

export function LoanCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState("required");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const createMut = useCreateLoan();
  const { data: empData } = useEmployees({ search: employeeSearch, page_size: 20 });
  const employees = empData?.results ?? [];
  const DIRECTOR_THRESHOLD = 300000;

  const amountVal = Form.useWatch("requested_amount", form);
  const exceedsThreshold = useMemo(
    () => amountVal && Number(amountVal) > DIRECTOR_THRESHOLD,
    [amountVal],
  );

  const onSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (!selectedEmployee) {
        message.error(t("loans.selectEmployee"));
        return;
      }
      await createMut.mutateAsync({
        employee: selectedEmployee.id,
        requested_amount: values.requested_amount,
        reason: values.reason,
        description: values.description || "",
      });
      message.success(t("loans.created"));
      navigate("/loans");
    } catch {
      // validation handled by form
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/loans")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-4 h-4" />{t("loans.back")}
        </button>
      </div>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-[#ffda2d] flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{t("loans.newLoan")}</h1>
            <p className="text-sm text-gray-500">{t("loans.createNewRecord")}</p>
          </div>
        </div>

        <Form form={form} layout="vertical" onFinish={onSubmit}>
          <Tabs activeKey={activeTab} onChange={setActiveTab} type="card" size="large"
            items={[
              {
                key: "required",
                label: <span className="flex items-center gap-2"><User className="w-4 h-4" />{t("loans.tabRequired")}</span>,
                children: (
                  <div className="grid grid-cols-1 gap-4 pt-4">
                    <Form.Item label={t("loans.employee")} required
                      help={selectedEmployee ? `${selectedEmployee.full_name || `${selectedEmployee.first_name} ${selectedEmployee.last_name}`} (${selectedEmployee.matricule})` : undefined}>
                      {!selectedEmployee ? (
                        <Select showSearch value={undefined}
                          onSearch={setEmployeeSearch}
                          onSelect={(value, option: any) => setSelectedEmployee(option.emp)}
                          placeholder={t("loans.searchEmployee")}
                          className="w-full" filterOption={false} notFoundContent={null}>
                          {employees.map((emp: any) => (
                            <Select.Option key={emp.id} value={emp.id} emp={emp}>
                              {emp.full_name || `${emp.first_name} ${emp.last_name}`} ({emp.matricule})
                            </Select.Option>
                          ))}
                        </Select>
                      ) : (
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <div>
                            <p className="text-sm font-bold">{selectedEmployee.full_name || `${selectedEmployee.first_name} ${selectedEmployee.last_name}`}</p>
                            <p className="text-xs text-gray-400">{selectedEmployee.matricule} — {selectedEmployee.department_name}</p>
                          </div>
                          <Button size="small" onClick={() => { setSelectedEmployee(null); form.setFieldsValue({ employee: undefined }); }}>
                            {t("loans.change")}
                          </Button>
                        </div>
                      )}
                    </Form.Item>

                    <Form.Item name="requested_amount" label={t("loans.requestedAmount")}
                      rules={[{ required: true, message: t("validation.required") },
                        { type: "number", min: 1, message: t("validation.positive") }]}
                      className="loan-amount-field">
                      <InputNumber className="w-full" min={1} placeholder={t("loans.amountPlaceholder")}
                        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, " ")}
                        parser={(value) => value?.replace(/\s/g, "") as any} />
                    </Form.Item>

                    <Form.Item name="reason" label={t("loans.reason")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <TextArea rows={3} placeholder={t("loans.reasonPlaceholder")} />
                    </Form.Item>
                  </div>
                ),
              },
              {
                key: "details",
                label: <span className="flex items-center gap-2"><FileText className="w-4 h-4" />{t("loans.tabDetails")}</span>,
                children: (
                  <div className="grid grid-cols-1 gap-4 pt-4">
                    <Form.Item name="description" label={t("loans.description")}>
                      <TextArea rows={4} placeholder={t("loans.descriptionPlaceholder")} />
                    </Form.Item>
                    <Form.Item name="notes" label={t("loans.notes")}>
                      <TextArea rows={3} placeholder={t("loans.notesPlaceholder")} />
                    </Form.Item>
                  </div>
                ),
              },
              {
                key: "preview",
                label: <span className="flex items-center gap-2"><CheckCircle className="w-4 h-4" />{t("loans.tabPreview")}</span>,
                children: (
                  <div className="space-y-4 pt-4">
                    <div className="bg-gray-50 rounded-xl p-4 space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">{t("loans.employee")}</span>
                        <span className="font-medium">{selectedEmployee ? `${selectedEmployee.full_name || `${selectedEmployee.first_name} ${selectedEmployee.last_name}`} (${selectedEmployee.matricule})` : "—"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">{t("loans.requestedAmount")}</span>
                        <span className="font-medium">{form.getFieldValue("requested_amount") ? `${Number(form.getFieldValue("requested_amount")).toLocaleString("fr-DZ")} DZD` : "—"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">{t("loans.reason")}</span>
                        <span className="font-medium text-right max-w-[60%]">{form.getFieldValue("reason") || "—"}</span>
                      </div>
                      {form.getFieldValue("description") && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">{t("loans.description")}</span>
                          <span className="font-medium text-right max-w-[60%]">{form.getFieldValue("description")}</span>
                        </div>
                      )}
                    </div>
                    {exceedsThreshold && (
                      <Alert
                        type="warning"
                        icon={<AlertTriangle className="w-4 h-4" />}
                        message={t("loans.directorApprovalRequired")}
                        description={t("loans.directorApprovalDesc", { amount: Number(DIRECTOR_THRESHOLD).toLocaleString("fr-DZ") })}
                        className="rounded-xl"
                        showIcon
                      />
                    )}
                    <p className="text-xs text-gray-400">{t("loans.submitInfo")}</p>
                  </div>
                ),
              },
            ]}
          />

          <div className="flex justify-end gap-3 pt-6 mt-6 border-t border-gray-100">
            <Button onClick={() => navigate("/loans")}>{t("common.cancel")}</Button>
            <Button type="primary" htmlType="submit" loading={createMut.isPending}
              icon={<Save className="w-4 h-4" />}
              style={{ background: "#ffda2d", borderColor: "#ffda2d", color: "#1a1917" }}>
              {t("loans.createLoan")}
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
