"""
Finance tests — modèles, services, API.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────
@pytest.fixture
def admin_user(db):
    return User.objects.create_user(email="admin@f.dz", password="P@ss!", first_name="A", last_name="D", role="admin")

@pytest.fixture
def comptable(db):
    return User.objects.create_user(email="comp@f.dz", password="P@ss!", first_name="C", last_name="D", role="comptable")

@pytest.fixture
def gestionnaire(db):
    return User.objects.create_user(email="gest@f.dz", password="P@ss!", first_name="G", last_name="D", role="gestionnaire")

@pytest.fixture
def fiscal_year(db, admin_user):
    from apps.finance.models import FiscalYear
    today = date.today()
    return FiscalYear.objects.create(
        year=today.year, label=f"Exercice {today.year}",
        start_date=date(today.year, 1, 1), end_date=date(today.year, 12, 31),
        status="open", total_budget=Decimal("10000000"),
        created_by=admin_user,
    )

@pytest.fixture
def department(db, admin_user):
    from apps.departments.models import Department
    return Department.objects.create(code="FIN", name="Finance", created_by=admin_user)

@pytest.fixture
def employee(db, department, admin_user):
    from apps.employees.models import Employee
    return Employee.objects.create(
        first_name="Emp", last_name="Test", gender="M",
        date_of_birth=date(1985,1,1), department=department,
        job_title="Agent", date_hired=date(2010,1,1), status="active",
        bank_account="CCP-123456", created_by=admin_user,
    )

@pytest.fixture
def benefit_type(db, admin_user):
    from apps.benefits.models import BenefitType
    return BenefitType.objects.create(
        code="MED01", name="Médical", category="medical",
        max_amount=100000, created_by=admin_user,
    )

@pytest.fixture
def budget(db, fiscal_year, benefit_type, admin_user):
    from apps.finance.models import Budget
    b = Budget.objects.create(
        fiscal_year=fiscal_year, benefit_type=benefit_type,
        code="BUD-MED", label="Budget Médical 2024",
        allocated_amount=Decimal("5000000"), status="approved",
        created_by=admin_user,
    )
    b.approved_by = admin_user
    b.save()
    return b

@pytest.fixture
def validated_benefit(db, employee, benefit_type, admin_user):
    from apps.benefits.models import Benefit
    from apps.benefits.services import BenefitService
    b = Benefit.objects.create(
        employee=employee, benefit_type=benefit_type,
        title="Test", requested_amount=Decimal("45000"),
        approved_amount=Decimal("45000"),
        workflow_state="validated", created_by=admin_user,
    )
    return b

def auth(client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    t = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {t.access_token}")
    return client


# ═══════════════════════════════════════════════════════════
# TESTS MODÈLES
# ═══════════════════════════════════════════════════════════
class TestFiscalYear:
    def test_consumption_rate_zero(self, fiscal_year):
        assert fiscal_year.consumption_rate == Decimal("0")

    def test_consumption_rate_partial(self, fiscal_year):
        fiscal_year.total_paid = Decimal("2500000")
        assert fiscal_year.consumption_rate == Decimal("25.00")

    def test_available_budget(self, fiscal_year):
        fiscal_year.total_paid      = Decimal("2000000")
        fiscal_year.total_committed = Decimal("1000000")
        assert fiscal_year.available_budget == Decimal("7000000")

    def test_is_active(self, fiscal_year):
        assert fiscal_year.is_active is True

    def test_is_not_active_when_draft(self, fiscal_year):
        fiscal_year.status = "draft"
        assert fiscal_year.is_active is False


class TestBudget:
    def test_available_amount(self, budget):
        budget.paid_amount      = Decimal("1000000")
        budget.committed_amount = Decimal("500000")
        assert budget.available_amount == Decimal("3500000")

    def test_consumption_rate(self, budget):
        budget.paid_amount      = Decimal("2000000")
        budget.committed_amount = Decimal("500000")
        rate = budget.consumption_rate
        assert rate == Decimal("50.00")

    def test_alert_triggered(self, budget):
        budget.paid_amount      = Decimal("4200000")
        budget.committed_amount = Decimal("100000")
        assert budget.is_alert_triggered is True

    def test_overrun_detected(self, budget):
        budget.paid_amount = Decimal("5500000")
        assert budget.is_overrun is True

    def test_budget_check_available(self, budget):
        from apps.finance.services import BudgetService
        ok, msg = BudgetService().check_budget_availability(budget, Decimal("100000"))
        assert ok is True

    def test_budget_check_insufficient(self, budget):
        from apps.finance.services import BudgetService
        ok, msg = BudgetService().check_budget_availability(budget, Decimal("9999999"))
        assert ok is False
        assert "insuffisant" in msg.lower()


class TestPayment:
    def test_reference_generated(self, db, validated_benefit, fiscal_year, admin_user):
        from apps.finance.services import PaymentService
        p = PaymentService().create_from_benefit(
            validated_benefit, fiscal_year=fiscal_year, user=admin_user
        )
        assert p.reference.startswith("PAY-")

    def test_net_amount_calculated(self, db, validated_benefit, fiscal_year, admin_user):
        from apps.finance.services import PaymentService
        p = PaymentService().create_from_benefit(
            validated_benefit, fiscal_year=fiscal_year, user=admin_user
        )
        assert p.net_amount == p.amount - p.fees

    def test_amount_from_approved(self, db, validated_benefit, fiscal_year, admin_user):
        from apps.finance.services import PaymentService
        validated_benefit.approved_amount = Decimal("40000")
        validated_benefit.save()
        p = PaymentService().create_from_benefit(
            validated_benefit, fiscal_year=fiscal_year, user=admin_user
        )
        assert p.amount == Decimal("40000")

    def test_duplicate_payment_raises(self, db, validated_benefit, fiscal_year, admin_user):
        from apps.finance.services import PaymentService, FinanceValidationError
        svc = PaymentService()
        svc.create_from_benefit(validated_benefit, fiscal_year=fiscal_year, user=admin_user)
        with pytest.raises(FinanceValidationError) as exc:
            svc.create_from_benefit(validated_benefit, fiscal_year=fiscal_year, user=admin_user)
        assert "DUPLICATE_PAYMENT" in exc.value.code

    def test_cannot_pay_unapproved(self, db, validated_benefit, fiscal_year, admin_user, comptable):
        from apps.finance.services import PaymentService, FinanceValidationError
        p = PaymentService().create_from_benefit(
            validated_benefit, fiscal_year=fiscal_year, user=admin_user
        )
        with pytest.raises(FinanceValidationError):
            PaymentService().mark_paid(p, "REF-001", user=comptable)

    def test_full_payment_cycle(self, db, validated_benefit, fiscal_year, budget, admin_user, comptable):
        from apps.finance.services import PaymentService
        from apps.finance.models import FinancialEntry
        svc = PaymentService()
        # Créer
        p = svc.create_from_benefit(validated_benefit, budget=budget, fiscal_year=fiscal_year, user=admin_user)
        assert p.status == "pending"
        # Approuver
        p = svc.approve(p, user=comptable)
        assert p.status == "approved"
        # Payer
        p = svc.mark_paid(p, "VIR-2024-001", user=comptable)
        assert p.status == "paid"
        assert p.bank_reference == "VIR-2024-001"
        # Écritures comptables (engagement + règlement)
        entries = FinancialEntry.objects.filter(payment=p)
        assert entries.count() == 2
        types = set(entries.values_list("entry_type", flat=True))
        assert "debit" in types
        assert "credit" in types

    def test_cancel_pending_payment(self, db, validated_benefit, fiscal_year, admin_user):
        from apps.finance.services import PaymentService
        svc = PaymentService()
        p = svc.create_from_benefit(validated_benefit, fiscal_year=fiscal_year, user=admin_user)
        p = svc.cancel(p, "Test annulation", user=admin_user)
        assert p.status == "cancelled"

    def test_cannot_cancel_paid_payment(self, db, validated_benefit, fiscal_year, admin_user, comptable):
        from apps.finance.services import PaymentService, FinanceValidationError
        svc = PaymentService()
        p = svc.create_from_benefit(validated_benefit, fiscal_year=fiscal_year, user=admin_user)
        p = svc.approve(p, user=comptable)
        p = svc.mark_paid(p, "REF-002", user=comptable)
        with pytest.raises(FinanceValidationError) as exc:
            svc.cancel(p, "Impossible", user=admin_user)
        assert "CANNOT_CANCEL_PAID" in exc.value.code

    def test_accounting_entry_immutable(self, db, validated_benefit, fiscal_year, admin_user):
        from apps.finance.services import PaymentService
        from apps.finance.models import FinancialEntry
        svc = PaymentService()
        svc.create_from_benefit(validated_benefit, fiscal_year=fiscal_year, user=admin_user)
        entry = FinancialEntry.objects.first()
        with pytest.raises(PermissionError):
            entry.label = "MODIFIÉ"
            entry.save()


# ═══════════════════════════════════════════════════════════
# TESTS API
# ═══════════════════════════════════════════════════════════
class TestFinanceAPI:
    def test_fiscal_year_list(self, db, fiscal_year, comptable):
        client = auth(APIClient(), comptable)
        r = client.get("/api/v1/finance/fiscal-years/")
        assert r.status_code == 200

    def test_active_fiscal_year(self, db, fiscal_year, admin_user):
        client = auth(APIClient(), admin_user)
        r = client.get("/api/v1/finance/fiscal-years/active/")
        assert r.status_code == 200
        assert r.json()["data"]["year"] == fiscal_year.year

    def test_create_payment_api(self, db, validated_benefit, fiscal_year, budget, comptable):
        client = auth(APIClient(), comptable)
        r = client.post("/api/v1/finance/payments/", {
            "benefit_id":     str(validated_benefit.id),
            "fiscal_year_id": str(fiscal_year.id),
            "budget_id":      str(budget.id),
            "payment_method": "virement",
        }, format="json")
        assert r.status_code == 201
        assert r.json()["data"]["status"] == "pending"

    def test_approve_payment_api(self, db, validated_benefit, fiscal_year, comptable):
        from apps.finance.services import PaymentService
        p = PaymentService().create_from_benefit(
            validated_benefit, fiscal_year=fiscal_year, user=comptable
        )
        client = auth(APIClient(), comptable)
        r = client.post(f"/api/v1/finance/payments/{p.id}/approve/")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "approved"

    def test_mark_paid_api(self, db, validated_benefit, fiscal_year, comptable):
        from apps.finance.services import PaymentService
        svc = PaymentService()
        p   = svc.create_from_benefit(validated_benefit, fiscal_year=fiscal_year, user=comptable)
        p   = svc.approve(p, user=comptable)
        client = auth(APIClient(), comptable)
        r = client.post(f"/api/v1/finance/payments/{p.id}/mark-paid/", {
            "bank_reference": "VIR-API-001",
        }, format="json")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "paid"

    def test_dashboard_api(self, db, fiscal_year, comptable):
        client = auth(APIClient(), comptable)
        r = client.get(f"/api/v1/finance/dashboard/?fiscal_year={fiscal_year.id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "fiscal_year" in data
        assert "payments"    in data
        assert "budgets"     in data

    def test_gestionnaire_cannot_approve_payment(self, db, validated_benefit, fiscal_year, gestionnaire, comptable):
        from apps.finance.services import PaymentService
        p = PaymentService().create_from_benefit(
            validated_benefit, fiscal_year=fiscal_year, user=comptable
        )
        client = auth(APIClient(), gestionnaire)
        r = client.post(f"/api/v1/finance/payments/{p.id}/approve/")
        assert r.status_code == 403

    def test_budget_consumption_report(self, db, fiscal_year, budget, admin_user):
        client = auth(APIClient(), admin_user)
        r = client.get(f"/api/v1/finance/budgets/consumption-report/?fiscal_year={fiscal_year.id}")
        assert r.status_code == 200
        assert r.json()["count"] >= 1

    def test_unauthenticated_blocked(self):
        r = APIClient().get("/api/v1/finance/payments/")
        assert r.status_code == 401
