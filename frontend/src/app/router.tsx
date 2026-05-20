import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import { AppLayout }      from "@shared/components/layout/AppLayout";
import { ProtectedRoute } from "@shared/components/layout/ProtectedRoute";
import { PageLoader }     from "@shared/components/ui/PageLoader";

const lz = (fn: () => Promise<Record<string, React.ComponentType>>, name: string) =>
  lazy(() => fn().then(m => ({ default: m[name] })));

const LoginPage          = lz(() => import("@modules/auth/pages/LoginPage"),                    "LoginPage");
const DashboardPage      = lz(() => import("@modules/dashboard/pages/DashboardPage"),           "DashboardPage");
const EmployeesPage      = lz(() => import("@modules/employees/pages/EmployeesListPage"),        "EmployeesPage");
const EmployeeDetailPage = lz(() => import("@modules/employees/pages/EmployeeDetailPage"),       "EmployeeDetailPage");
const BenefitsPage       = lz(() => import("@modules/benefits/pages/BenefitsListPage"),          "BenefitsPage");
const BenefitDetailPage  = lz(() => import("@modules/benefits/pages/BenefitDetailPage"),         "BenefitDetailPage");
const FinanceDashboard   = lz(() => import("@modules/finance/pages/FinanceDashboardPage"),       "FinanceDashboardPage");
const PaymentsPage       = lz(() => import("@modules/finance/pages/PaymentsPage"),               "PaymentsPage");
const BudgetsPage        = lz(() => import("@modules/finance/pages/BudgetsPage"),                "BudgetsPage");
const ConventionDash     = lz(() => import("@modules/conventions/pages/ConventionsDashboardPage"), "ConventionsDashboardPage");
const ConventionDetail   = lz(() => import("@modules/conventions/pages/ConventionDetailPage"),     "ConventionDetailPage");
const ConventionCreate   = lz(() => import("@modules/conventions/pages/ConventionCreatePage"),     "ConventionCreatePage");
const PartnersPage       = lz(() => import("@modules/conventions/pages/PartnersPage"),             "PartnersPage");
const UsersPage          = lz(() => import("@modules/users/pages/UsersPage"),                    "UsersPage");
const AnalyticsDashPage  = lz(() => import("@modules/analytics/pages/AnalyticsDashboardPage"),   "AnalyticsDashboardPage");
const BeneficiariesPage  = lz(() => import("@modules/beneficiaries/pages/BeneficiariesListPage"), "BeneficiariesListPage");
const ReportsPage        = lz(() => import("@modules/analytics/pages/ReportsPage"),               "ReportsPage");
const DecisionSupportPage = lz(() => import("@modules/analytics/pages/DecisionSupportPage"),      "DecisionSupportPage");
const NotificationPrefsPage = lz(() => import("@modules/notifications/pages/NotificationPreferencesPage"), "NotificationPreferencesPage");
const MonitoringPage = lz(() => import("@modules/monitoring/pages/MonitoringDashboardPage"), "MonitoringDashboardPage");
const AIAssistantPage  = lz(() => import("@modules/ai/pages/AIAssistantPage"),                 "AIAssistantPage");
const NotFoundPage       = lz(() => import("@shared/components/ui/NotFoundPage"),               "NotFoundPage");
const ForbiddenPage      = lz(() => import("@shared/components/ui/ForbiddenPage"),              "ForbiddenPage");

const W = (C: React.ComponentType) => <Suspense fallback={<PageLoader />}><C /></Suspense>;

const router = createBrowserRouter([
  { path: "/login", element: W(LoginPage)     },
  { path: "/403",   element: W(ForbiddenPage) },
  {
    element: <ProtectedRoute />,
    children: [{
      element: <AppLayout />,
      children: [
        { path: "/",          element: <Navigate to="/dashboard" replace /> },
        { path: "/dashboard", element: W(DashboardPage) },
        { path: "/benefits",     element: W(BenefitsPage) },
        { path: "/benefits/:id", element: W(BenefitDetailPage) },
        // Employees — admin, gestionnaire, comptable
        { element: <ProtectedRoute roles={["admin","gestionnaire","comptable"]} />, children: [
          { path: "/employees",     element: W(EmployeesPage) },
          { path: "/employees/:id", element: W(EmployeeDetailPage) },
        ]},
        // Finance — admin, comptable
        { element: <ProtectedRoute roles={["admin","comptable"]} />, children: [
          { path: "/finance",          element: W(FinanceDashboard) },
          { path: "/finance/payments", element: W(PaymentsPage) },
          { path: "/finance/budgets",  element: W(BudgetsPage) },
        ]},
        // Conventions — admin, gestionnaire, comptable
        { element: <ProtectedRoute roles={["admin","gestionnaire","comptable"]} />, children: [
          { path: "/conventions",            element: W(ConventionDash) },
          { path: "/conventions/partners",   element: W(PartnersPage) },
          { path: "/conventions/new",        element: W(ConventionCreate) },
          { path: "/conventions/:id",        element: W(ConventionDetail) },
        ]},
        // Analytics & Reporting
        { path: "/reporting", element: W(ReportsPage) },
        { element: <ProtectedRoute roles={["admin"]} />, children: [
          { path: "/analytics",            element: W(AnalyticsDashPage) },
          { path: "/analytics/decisions",   element: W(DecisionSupportPage) },
        ]},
        // Admin
        { element: <ProtectedRoute roles={["admin"]} />, children: [
          { path: "/users",       element: W(UsersPage) },
          { path: "/settings",    element: W(NotFoundPage) },
          { path: "/monitoring",  element: W(MonitoringPage) },
          { path: "/ai/assistant", element: W(AIAssistantPage) },
        ]},
        // Notification preferences
        { element: <ProtectedRoute />, children: [
          { path: "/preferences/notifications", element: W(NotificationPrefsPage) },
        ]},
        { element: <ProtectedRoute roles={["admin","gestionnaire"]} />, children: [
          { path: "/beneficiaries", element: W(BeneficiariesPage) },
        ]},
      ],
    }],
  },
  { path: "*", element: W(NotFoundPage) },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
