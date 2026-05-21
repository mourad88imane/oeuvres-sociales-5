"""Tests for reporting AggregationService."""

from datetime import date

import pytest

from apps.reporting.services import AggregationService
from django.test import TestCase
from django.utils import timezone

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


class TestAggregationService(TestCase):
    def setUp(self):
        self.svc = AggregationService()
        # Create test data across apps
        from apps.beneficiaries.models import Beneficiary
        from apps.departments.models import Department
        from apps.employees.models import Employee
        from apps.finance.models import Budget, FiscalYear, Payment
        from apps.benefits.models import Benefit, BenefitType

        dept = Department.objects.create(code="DEPT01", name="Test Dept")
        emp = Employee.objects.create(
            matricule="EMP001",
            first_name="Test",
            last_name="User",
            email_professional="test@test.com",
            department=dept,
            status="active",
            gender="M",
            date_of_birth=date(1990, 1, 1),
            date_hired=date(2020, 1, 1),
            job_title="Engineer",
        )
        # Beneficiary
        Beneficiary.objects.create(
            employee=emp,
            first_name="Child",
            last_name="Test",
            gender="M",
            date_of_birth=date(2010, 1, 1),
            relationship="child",
        )
        # Fiscal year + budget + payment
        fy = FiscalYear.objects.create(
            year=timezone.now().year,
            label=f"FY {timezone.now().year}",
            start_date=date(timezone.now().year, 1, 1),
            end_date=date(timezone.now().year, 12, 31),
            status="open",
        )
        budget = Budget.objects.create(
            fiscal_year=fy,
            code="BGT001",
            label="Test Budget",
            allocated_amount=1_000_000,
        )
        bt = BenefitType.objects.create(
            code="MED",
            name="Medical",
            category="medical",
        )
        benefit = Benefit.objects.create(
            employee=emp,
            benefit_type=bt,
            requested_amount=100_000,
            title="Test Benefit",
        )
        Payment.objects.create(
            employee=emp,
            budget=budget,
            benefit=benefit,
            fiscal_year=fy,
            amount=100_000,
            status="paid",
            executed_date=timezone.now().date(),
        )
        self.emp = emp
        self.fy = fy
        self.budget = budget

    def test_get_global_stats_returns_all_sections(self):
        stats = self.svc.get_global_stats()
        self.assertIn("employees", stats)
        self.assertIn("beneficiaries", stats)
        self.assertIn("benefits", stats)
        self.assertIn("conventions", stats)
        self.assertIn("finance", stats)

    def test_get_global_stats_employee_counts(self):
        stats = self.svc.get_global_stats()
        self.assertEqual(stats["employees"]["total"], 1)
        self.assertEqual(stats["employees"]["active"], 1)

    def test_get_monthly_trends_returns_list(self):
        trends = self.svc.get_monthly_trends(months=3)
        self.assertIsInstance(trends, list)
        if trends:
            self.assertIn("month", trends[0])

    def test_get_all_kpis_returns_list(self):
        kpis = self.svc.get_all_kpis()
        self.assertIsInstance(kpis, list)
        self.assertTrue(len(kpis) > 0)

    def test_compute_and_snapshot_kpis_creates_snapshots(self):
        from apps.reporting.models import KpiSnapshot

        data = self.svc.compute_and_snapshot_kpis()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        snapshots = KpiSnapshot.objects.filter(date=timezone.localdate())
        self.assertEqual(snapshots.count(), len(data))
