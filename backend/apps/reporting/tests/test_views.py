"""Tests for reporting API viewsets."""
import io
import json
import pytest
from datetime import date

pytestmark = [pytest.mark.django_db, pytest.mark.integration]

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


class TestAnalyticsViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        from apps.users.models import CustomUser
        self.user = CustomUser.objects.create_user(
            email="admin@test.com", password="test123", role="admin"
        )
        self.client.force_authenticate(self.user)

    def test_summary_endpoint(self):
        resp = self.client.get("/api/v1/reporting/analytics/summary/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "success")
        self.assertIn("data", resp.data)

    def test_trends_endpoint(self):
        resp = self.client.get("/api/v1/reporting/analytics/trends/?months=6")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.data["data"], list)

    def test_global_data_endpoint(self):
        resp = self.client.get("/api/v1/reporting/analytics/global_data/")
        self.assertEqual(resp.status_code, 200)
        for key in ("summary", "trends", "top", "kpis"):
            self.assertIn(key, resp.data["data"])

    def test_predictions_endpoint(self):
        resp = self.client.get("/api/v1/reporting/analytics/predictions/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("benefits_trend", resp.data["data"])
        self.assertIn("budget_consumption", resp.data["data"])

    def test_anomalies_endpoint(self):
        resp = self.client.get("/api/v1/reporting/analytics/anomalies/?days=30")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("anomalies", resp.data["data"])

    def test_decisions_endpoint(self):
        resp = self.client.get("/api/v1/reporting/analytics/decisions/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("recommendations", resp.data["data"])


class TestKpiViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        from apps.users.models import CustomUser
        self.user = CustomUser.objects.create_user(
            email="admin@test.com", password="test123", role="admin"
        )
        self.client.force_authenticate(self.user)

        from apps.reporting.models import KpiDefinition
        self.kpi = KpiDefinition.objects.create(
            code="test_kpi", name="Test KPI",
            category="global", target_value=100.0,
        )

    def test_list_kpis(self):
        resp = self.client.get("/api/v1/reporting/kpis/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.data["results"]) > 0)

    def test_kpi_values_endpoint(self):
        resp = self.client.get("/api/v1/reporting/kpis/values/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.data["data"], list)

    def test_kpi_snapshot(self):
        resp = self.client.post("/api/v1/reporting/kpis/snapshot/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.data["data"], list)

    def test_kpi_history_endpoint(self):
        # First create a snapshot
        self.client.post("/api/v1/reporting/kpis/snapshot/")
        resp = self.client.get(
            f"/api/v1/reporting/kpis/history/?code={self.kpi.code}"
        )
        self.assertEqual(resp.status_code, 200)


class TestReportViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        from apps.users.models import CustomUser
        self.user = CustomUser.objects.create_user(
            email="admin@test.com", password="test123", role="admin"
        )
        self.client.force_authenticate(self.user)

        from apps.reporting.models import ReportDefinition
        self.report = ReportDefinition.objects.create(
            code="test_report", title="Test Report",
            category="employees", default_format="csv",
            is_system=True,
        )
        self.employee_report = ReportDefinition.objects.create(
            code="emp_report", title="Employee Report",
            category="employees",
        )

    def test_list_reports(self):
        resp = self.client.get("/api/v1/reporting/reports/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)

    def test_generate_csv_report(self):
        resp = self.client.post(
            f"/api/v1/reporting/reports/{self.employee_report.id}/generate/",
            {"format": "csv"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "success")

    def test_generate_json_report(self):
        resp = self.client.post(
            f"/api/v1/reporting/reports/{self.employee_report.id}/generate/",
            {"format": "json"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_generate_excel_report(self):
        resp = self.client.post(
            f"/api/v1/reporting/reports/{self.employee_report.id}/generate/",
            {"format": "excel"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_generate_pdf_report(self):
        resp = self.client.post(
            f"/api/v1/reporting/reports/{self.employee_report.id}/generate/",
            {"format": "pdf"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_generate_with_invalid_format_falls_back_to_csv(self):
        resp = self.client.post(
            f"/api/v1/reporting/reports/{self.employee_report.id}/generate/",
            {"format": "invalid_fallback"},
        )
        self.assertEqual(resp.status_code, 200)


class TestExportViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        from apps.users.models import CustomUser
        self.user = CustomUser.objects.create_user(
            email="admin@test.com", password="test123", role="admin"
        )
        self.client.force_authenticate(self.user)

    def test_list_exports(self):
        resp = self.client.get("/api/v1/reporting/exports/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)


class TestDashboardEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()
        from apps.users.models import CustomUser
        self.user = CustomUser.objects.create_user(
            email="admin@test.com", password="test123", role="admin"
        )
        self.client.force_authenticate(self.user)

    def test_dashboard_global_endpoint(self):
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 200)
        for key in ("summary", "trends", "top", "kpis", "date"):
            self.assertIn(key, resp.data.get("data", {}))
