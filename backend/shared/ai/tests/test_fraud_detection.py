from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@t.dz", password="P@ss123!",
        first_name="Admin", last_name="Test", role="admin",
    )


@pytest.fixture
def department(db, admin_user):
    from apps.departments.models import Department
    return Department.objects.create(code="IT", name="IT", created_by=admin_user)


@pytest.fixture
def employee(db, department, admin_user):
    from apps.employees.models import Employee
    return Employee.objects.create(
        first_name="John", last_name="Doe", gender="M",
        date_of_birth=date(1990, 5, 15), department=department,
        job_title="Dev", date_hired=date(2015, 1, 1),
        status="active", created_by=admin_user,
    )


@pytest.fixture
def benefit(db, employee, admin_user):
    from apps.benefits.models import Benefit
    return Benefit.objects.create(
        employee=employee,
        benefit_type="medical",
        amount=10000,
        status="approved",
        created_by=admin_user,
    )


@pytest.fixture
def payment(db, benefit, admin_user):
    from apps.finance.models import Payment
    return Payment.objects.create(
        benefit=benefit,
        amount=50000,
        status="paid",
        executed_date=timezone.now().date(),
        created_by=admin_user,
    )


class TestFraudDetectorRules:

    def test_duplicate_payment_detection(self, payment, admin_user):
        from apps.finance.models import Payment
        dup = Payment.objects.create(
            benefit=payment.benefit,
            amount=payment.amount,
            status="paid",
            executed_date=payment.executed_date,
            created_by=admin_user,
        )
        from shared.ai.fraud_detection import fraud_detector
        results = fraud_detector._detect_duplicate_payments(365)
        assert len(results) >= 1
        assert results[0]["rule"] == "duplicate_payment"

    def test_unusual_amount_detection(self, payment, admin_user):
        from apps.finance.models import Payment
        for _ in range(10):
            Payment.objects.create(
                benefit=payment.benefit,
                amount=1000,
                status="paid",
                executed_date=timezone.now().date(),
                created_by=admin_user,
            )
        outlier = Payment.objects.create(
            benefit=payment.benefit,
            amount=9999999,
            status="paid",
            executed_date=timezone.now().date(),
            created_by=admin_user,
        )
        from shared.ai.fraud_detection import fraud_detector
        results = fraud_detector._detect_unusual_amounts(365)
        assert len(results) >= 1
        assert outlier.id and any(r["target_id"] == str(outlier.id) for r in results)

    def test_threshold_proximity(self, payment, admin_user):
        from apps.finance.models import Payment
        near = Payment.objects.create(
            benefit=payment.benefit,
            amount=48000,
            status="paid",
            executed_date=timezone.now().date(),
            created_by=admin_user,
        )
        from shared.ai.fraud_detection import fraud_detector
        results = fraud_detector._detect_threshold_proximity(365)
        assert any(r["target_id"] == str(near.id) for r in results)

    def test_amount_rounding(self, payment, admin_user):
        from apps.finance.models import Payment
        round_amt = Payment.objects.create(
            benefit=payment.benefit,
            amount=100000,
            status="paid",
            executed_date=timezone.now().date(),
            created_by=admin_user,
        )
        from shared.ai.fraud_detection import fraud_detector
        results = fraud_detector._detect_amount_rounding(365)
        assert any(r["target_id"] == str(round_amt.id) for r in results)

    def test_detect_all_runs_without_error(self, payment, admin_user):
        from shared.ai.fraud_detection import fraud_detector
        results = fraud_detector.detect_all(days=365, save=False)
        assert "total_flags" in results
        assert "rules_triggered" in results
        assert "flags" in results

    def test_detect_all_saves_flags(self, payment, admin_user):
        from apps.finance.models import Payment
        Payment.objects.create(
            benefit=payment.benefit,
            amount=payment.amount,
            status="paid",
            executed_date=payment.executed_date,
            created_by=admin_user,
        )
        from shared.ai.fraud_detection import fraud_detector
        results = fraud_detector.detect_all(days=365, save=True)
        assert results["total_flags"] > 0
        from shared.ai.models import AIAnomaly
        anomalies = AIAnomaly.objects.filter(
            detection_method__startswith="fraud_"
        )
        assert anomalies.count() > 0
