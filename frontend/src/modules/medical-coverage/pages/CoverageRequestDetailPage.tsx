import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button, Card, Tag, Descriptions, Modal, Input, message, Steps } from "antd";
import { ArrowLeft, Download, Printer, CheckCircle, XCircle } from "lucide-react";
import { useState } from "react";
import {
  useCoverageRequest,
  useTransitionCoverageRequest,
} from "../hooks/useCoverageRequests";
import { coverageRequestApi } from "../api/requests";
import { REQUEST_STATUS_UI, REQUEST_WORKFLOW_ORDER } from "../types/request";
import type { RequestStatus } from "../types/request";

export function CoverageRequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { data: request } = useCoverageRequest(id ?? null);
  const transitionMut = useTransitionCoverageRequest(id!);
  const [actionModal, setActionModal] = useState<{ to_state: string; label: string; requires_reason: boolean } | null>(null);
  const [reason, setReason] = useState("");

  const handleTransition = async () => {
    if (!actionModal) return;
    try {
      await transitionMut.mutateAsync({
        to_state: actionModal.to_state as RequestStatus,
        reason: actionModal.requires_reason ? reason : undefined,
      });
      message.success(`Demande ${actionModal.label.toLowerCase()}`);
      setActionModal(null);
      setReason("");
    } catch {
      message.error("Erreur lors de la transition");
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const resp = await coverageRequestApi.downloadPdf(id!);
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${request?.request_number}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      message.error("Erreur lors du téléchargement du PDF");
    }
  };

  if (!request) {
    return <div className="text-center py-12 text-gray-400">Chargement...</div>;
  }

  const ui = REQUEST_STATUS_UI[request.workflow_state as keyof typeof REQUEST_STATUS_UI] || {};
  const transitions = request.available_transitions ?? [];
  const currentStepIndex = REQUEST_WORKFLOW_ORDER.indexOf(request.workflow_state as RequestStatus);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/medical-coverage/requests")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-4 h-4" />Retour
        </button>
        <div className="flex gap-2">
          <Button icon={<Download className="w-4 h-4" />} onClick={handleDownloadPdf}>
            Télécharger PDF
          </Button>
          <Button icon={<Printer className="w-4 h-4" />} onClick={() => window.print()}>
            Imprimer
          </Button>
        </div>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold font-mono">{request.request_number}</h1>
            <Tag color={ui.color} className="mt-1">{ui.label}</Tag>
          </div>
        </div>

        <Steps current={currentStepIndex} size="small" className="mb-6" style={{ maxWidth: 600 }}
          items={REQUEST_WORKFLOW_ORDER.map(s => {
            const u = REQUEST_STATUS_UI[s];
            return { key: s, title: u?.label };
          })} />

        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="Catégorie">{request.category_display}</Descriptions.Item>
          <Descriptions.Item label="Partenaire">{request.partner_name}</Descriptions.Item>
          <Descriptions.Item label="Employé">{request.employee_name} ({request.employee_matricule})</Descriptions.Item>
          <Descriptions.Item label="Ayant droit">{request.beneficiary_name || "—"}</Descriptions.Item>
          <Descriptions.Item label="Date de couverture">{request.coverage_date}</Descriptions.Item>
          <Descriptions.Item label="Date de validation">{request.validation_date || "—"}</Descriptions.Item>
          <Descriptions.Item label="Observation" span={2}>{request.observation || "—"}</Descriptions.Item>
        </Descriptions>
      </Card>

      {transitions.length > 0 && (
        <Card title="Actions">
          <div className="flex flex-wrap gap-2">
            {transitions.filter(t => t.can_execute).map((t: any) => (
              <Button key={t.to_state}
                onClick={() => setActionModal({ to_state: t.to_state, label: t.label, requires_reason: t.requires_reason })}
                icon={t.severity === "HIGH" ? <XCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}>
                {t.label}
              </Button>
            ))}
          </div>
        </Card>
      )}

      <Modal title={actionModal?.label} open={!!actionModal} onOk={handleTransition}
        onCancel={() => { setActionModal(null); setReason(""); }}
        confirmLoading={transitionMut.isPending}
        okText="Confirmer" cancelText="Annuler">
        {actionModal?.requires_reason && (
          <Input.TextArea rows={3} value={reason} onChange={e => setReason(e.target.value)}
            placeholder="Motif obligatoire" />
        )}
        <p className="text-sm text-gray-500 mt-2">
          {actionModal ? `Voulez-vous ${actionModal.label.toLowerCase()} cette demande ?` : ""}
        </p>
      </Modal>
    </div>
  );
}
