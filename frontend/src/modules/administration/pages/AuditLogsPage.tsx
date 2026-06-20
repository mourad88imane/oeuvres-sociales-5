import { useEffect, useState } from "react";
import { Card, Table, Tag, DatePicker } from "antd";
import { ClipboardList } from "lucide-react";
import { fetchApprovalHistory } from "../api";

const ACTION_COLORS: Record<string, string> = {
  auto_validated: "green",
  approved: "green",
  rejected: "red",
  pending_manager: "orange",
  escalated: "purple",
  director_approved: "green",
  director_rejected: "red",
};

export function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApprovalHistory().then((r) => {
      setLogs(r.results ?? []);
      setLoading(false);
    });
  }, []);

  const columns = [
    { title: "Demande", dataIndex: "request_number", key: "request_number" },
    {
      title: "Action", dataIndex: "action", key: "action",
      render: (a: string) => (
        <Tag color={ACTION_COLORS[a] || "default"}>{a}</Tag>
      ),
    },
    { title: "Utilisateur", dataIndex: "user_name", key: "user_name" },
    { title: "Commentaire", dataIndex: "comment", key: "comment", ellipsis: true },
    {
      title: "Date", dataIndex: "date", key: "date",
      render: (d: string) => new Date(d).toLocaleString("fr-FR"),
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-[#ffda2d] flex items-center justify-center">
          <ClipboardList className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-xl font-bold">Journal d'Audit</h1>
          <p className="text-sm text-gray-500">Historique des approbations et rejets</p>
        </div>
      </div>
      <Card>
        <Table dataSource={logs} columns={columns} rowKey="id" loading={loading}
          pagination={{ pageSize: 20 }} size="middle" />
      </Card>
    </div>
  );
}
