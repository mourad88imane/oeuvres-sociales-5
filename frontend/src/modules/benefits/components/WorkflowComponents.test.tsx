import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { WorkflowBadge, WorkflowTimeline } from "./WorkflowComponents";
import type { Benefit } from "../types";

vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const map: Record<string, string> = {
          "benefits.rejected": "Rejetée",
          "benefits.cancelled": "Annulée",
          "benefits.pending": "En attente",
          "benefits.pendingDirectorApproval": "En attente d'approbation du directeur",
          "common.noData": "—",
        };
        return map[key] ?? key;
      },
      i18n: { language: "fr", changeLanguage: vi.fn() },
    }),
  };
});

const createMockBenefit = (overrides: Partial<Benefit> = {}): Benefit => ({
  id: "1",
  reference: "BEN-2024-00001",
  title: "Test Benefit",
  workflow_state: "draft",
  state_label: "Brouillon",
  state_config: { label: "Brouillon", color: "#999", bg: "#eee", text: "#333", is_initial: true, is_final: false, description: "" },
  employee: "emp1",
  employee_name: "John Doe",
  employee_matricule: "EMP001",
  department_name: "IT",
  benefit_type: "bt1",
  benefit_type_name: "Medical",
  benefit_type_code: "MED",
  benefit_category: "medical",
  requested_amount: 500000,
  approved_amount: null,
  paid_amount: null,
  amount_display: "500 000 DZD",
  priority: "normal",
  priority_display: "Normale",
  is_overdue: false,
  processing_days: null,
  submitted_at: null,
  validated_at: null,
  paid_at: null,
  due_date: null,
  attachments_count: 0,
  ai_anomaly_flag: false,
  risk_score: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  description: "",
  benefit_type_info: {} as any,
  beneficiary: null,
  payment_reference: "",
  payment_method: "",
  payment_method_display: "",
  rejection_reason: "",
  internal_notes: "",
  validated_by_name: null,
  paid_by_name: null,
  rejected_at: null,
  ai_score: null,
  ai_metadata: {},
  attachments: [],
  comments: [],
  available_transitions: [],
  last_transition_at: null,
  last_transition_reason: "",
  created_by_name: null,
  ...overrides,
});

describe("WorkflowBadge", () => {
  it("renders draft badge", () => {
    render(<WorkflowBadge state="draft" />);
    expect(screen.getByText("Brouillon")).toBeInTheDocument();
  });

  it("renders pending_director_approval badge", () => {
    render(<WorkflowBadge state="pending_director_approval" />);
    expect(screen.getByText("En attente du directeur")).toBeInTheDocument();
  });
});

describe("WorkflowTimeline", () => {
  it("renders timeline with draft benefit", () => {
    const benefit = createMockBenefit({ workflow_state: "draft" });
    const { container } = render(<WorkflowTimeline benefit={benefit} />);
    expect(container.querySelector(".space-y-1")).toBeTruthy();
  });

  it("shows pending_director_approval indicator when state is pending_director_approval", () => {
    const benefit = createMockBenefit({
      workflow_state: "pending_director_approval",
      last_transition_at: "2024-06-01T00:00:00Z",
    });
    render(<WorkflowTimeline benefit={benefit} />);
    expect(screen.getByText("En attente d'approbation du directeur")).toBeInTheDocument();
  });

  it("renders compact timeline correctly", () => {
    const benefit = createMockBenefit({ workflow_state: "draft" });
    const { container } = render(<WorkflowTimeline benefit={benefit} compact />);
    expect(container.querySelector(".flex.items-center.gap-1")).toBeTruthy();
  });

  it("shows escalated state in compact timeline", () => {
    const benefit = createMockBenefit({ workflow_state: "pending_director_approval" });
    render(<WorkflowTimeline benefit={benefit} compact />);
    expect(screen.getByText("En attente du directeur")).toBeInTheDocument();
  });
});
