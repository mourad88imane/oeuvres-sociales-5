import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Tabs, Form, Input, Select, DatePicker, Button, Card, message } from "antd";
import { ArrowLeft, Save, User, FileText } from "lucide-react";
import { useEmployees } from "@modules/employees/hooks/useEmployees";
import { beneficiaryGlobalApi } from "../api";

const { TextArea } = Input;
const { Option } = Select;

export function BeneficiaryCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState("required");
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const { data: empData } = useEmployees({ search: employeeSearch, page_size: 20 });
  const employees = empData?.results ?? [];

  const onSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await beneficiaryGlobalApi.createForEmployee(values.employee, {
        ...values,
        date_of_birth: values.date_of_birth?.format("YYYY-MM-DD"),
      });
      message.success(t("beneficiaries.created"));
      navigate("/beneficiaries");
    } catch {
      // validation handled by form
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/beneficiaries")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-4 h-4" />{t("beneficiaries.back")}
        </button>
      </div>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-[#ffda2d] flex items-center justify-center">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{t("beneficiaries.newBeneficiary")}</h1>
            <p className="text-sm text-gray-500">{t("beneficiaries.createNewRecord")}</p>
          </div>
        </div>

        <Form form={form} layout="vertical" onFinish={onSubmit}>
          <Tabs activeKey={activeTab} onChange={setActiveTab} type="card" size="large"
            items={[
              {
                key: "required",
                label: <span className="flex items-center gap-2"><User className="w-4 h-4" />{t("beneficiaries.tabRequired")}</span>,
                children: (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                    <Form.Item name="employee" label={t("beneficiaries.employee")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Select showSearch placeholder={t("beneficiaries.searchEmployee")}
                        filterOption={false} onSearch={setEmployeeSearch} notFoundContent={null}>
                        {employees.map((e: any) => (
                          <Option key={e.id} value={e.id}>{e.matricule} - {e.full_name}</Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <div />
                    <Form.Item name="last_name" label={t("beneficiaries.lastName")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Input placeholder={t("beneficiaries.lastNamePlaceholder")} />
                    </Form.Item>
                    <Form.Item name="first_name" label={t("beneficiaries.firstName")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Input placeholder={t("beneficiaries.firstNamePlaceholder")} />
                    </Form.Item>
                    <Form.Item name="last_name_ar" label={t("beneficiaries.lastNameAr")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name="first_name_ar" label={t("beneficiaries.firstNameAr")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name="gender" label={t("beneficiaries.gender")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Select placeholder={t("beneficiaries.selectGender")}>
                        <Option value="M">{t("beneficiaries.male")}</Option>
                        <Option value="F">{t("beneficiaries.female")}</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item name="date_of_birth" label={t("beneficiaries.dateOfBirth")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <DatePicker className="w-full" format="YYYY-MM-DD" />
                    </Form.Item>
                    <Form.Item name="relationship" label={t("beneficiaries.relationship")}
                      rules={[{ required: true, message: t("validation.required") }]}>
                      <Select placeholder={t("beneficiaries.selectRelationship")}>
                        <Option value="spouse">{t("beneficiaries.spouse")}</Option>
                        <Option value="child">{t("beneficiaries.child")}</Option>
                        <Option value="parent">{t("beneficiaries.parent")}</Option>
                      </Select>
                    </Form.Item>
                  </div>
                ),
              },
              {
                key: "additional",
                label: <span className="flex items-center gap-2"><FileText className="w-4 h-4" />{t("beneficiaries.tabAdditional")}</span>,
                children: (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                    <Form.Item name="phone" label={t("beneficiaries.phone")}>
                      <Input />
                    </Form.Item>
                    <Form.Item name="social_security_number" label={t("beneficiaries.ssn")}>
                      <Input />
                    </Form.Item>
                    <Form.Item name="address" label={t("beneficiaries.address")}>
                      <TextArea rows={2} />
                    </Form.Item>
                    <Form.Item name="notes" label={t("beneficiaries.notes")}>
                      <TextArea rows={2} />
                    </Form.Item>
                  </div>
                ),
              },
            ]}
          />

          <div className="flex justify-end gap-3 pt-6 mt-6 border-t border-gray-100">
            <Button onClick={() => navigate("/beneficiaries")}>{t("common.cancel")}</Button>
            <Button type="primary" htmlType="submit" loading={loading}
              icon={<Save className="w-4 h-4" />}
              style={{ background: "#ffda2d", borderColor: "#ffda2d", color: "#1a1917" }}>
              {t("beneficiaries.save")}
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}
