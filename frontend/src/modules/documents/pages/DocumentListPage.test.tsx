import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocumentListPage } from "./DocumentListPage";

vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => key,
      i18n: { language: "fr", changeLanguage: vi.fn() },
    }),
  };
});

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

vi.mock("../api/index", () => ({
  useDocuments: () => ({
    data: [
      {
        id: "1",
        title: "Contrat de travail",
        category: "contract",
        category_display: "Contrat",
        file_name: "contrat.pdf",
        file_size_bytes: 102400,
        file_type: "application/pdf",
        tags: ["urgent"],
        time_ago: "2 jours",
        created_at: "2025-01-01T00:00:00Z",
        download_url: "/media/documents/contrat.pdf",
      },
    ],
    isLoading: false,
    error: null,
  }),
  useDocumentCategories: () => ({
    data: [
      { value: "general", label: "Général" },
      { value: "contract", label: "Contrat" },
      { value: "report", label: "Rapport" },
    ],
  }),
  useUploadDocument: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteDocument: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <DocumentListPage />
    </QueryClientProvider>,
  );
};

describe("DocumentListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", () => {
    renderPage();
    expect(screen.getByText("Gestion des documents")).toBeInTheDocument();
  });

  it("renders document rows from the API", () => {
    renderPage();
    expect(screen.getByText("Contrat de travail")).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes("Contrat"))).toBeInTheDocument();
  });

  it("renders category filter tabs", () => {
    renderPage();
    expect(screen.getByText("Tous")).toBeInTheDocument();
  });
});
