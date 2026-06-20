from datetime import date

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@t.dz", password="P@ss123!",
        first_name="Admin", last_name="Test", role="admin",
    )


@pytest.fixture
def gestionnaire(db):
    return User.objects.create_user(
        email="gest@t.dz", password="P@ss123!",
        first_name="Gest", last_name="Test", role="gestionnaire",
    )


@pytest.fixture
def comptable(db):
    return User.objects.create_user(
        email="comp@t.dz", password="P@ss123!",
        first_name="Comp", last_name="Test", role="comptable",
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
def loan(db, employee, admin_user):
    from apps.loans.models import Loan
    return Loan.objects.create(
        employee=employee,
        requested_amount=50000,
        reason="Medical expenses",
        created_by=admin_user,
    )


@pytest.fixture
def api(db):
    from rest_framework.test import APIClient
    return APIClient()


def auth(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


# ═══════════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════════

class TestLoanModel:

    def test_initial_state_is_draft(self, loan):
        assert loan.workflow_state == "draft"

    def test_reference_generated(self, loan):
        assert loan.reference is not None
        assert loan.reference.startswith("PRET-")

    def test_str_contains_reference(self, loan):
        assert loan.reference in str(loan)

    def test_default_amounts_are_none(self, loan):
        assert loan.approved_amount is None
        assert loan.paid_amount is None

    def test_is_not_final_in_draft(self, loan):
        assert loan.is_final is False

    def test_paid_is_final(self, loan, admin_user):
        from apps.loans.models import Loan
        loan.workflow_state = "paid"
        loan.save(update_fields=["workflow_state"])
        loan = Loan.objects.get(pk=loan.pk)
        assert loan.is_final is True


# ═══════════════════════════════════════════════════════════
# WORKFLOW TRANSITION TESTS
# ═══════════════════════════════════════════════════════════

class TestWorkflowTransitions:

    def test_submit_transition(self, loan, admin_user):
        from apps.loans.services import LoanService
        result = LoanService().transition(loan, "submitted", user=admin_user)
        assert result.success is True
        assert result.to_state == "submitted"
        loan.refresh_from_db()
        assert loan.workflow_state == "submitted"
        assert loan.submitted_at is not None

    def test_submit_to_under_review(self, loan, admin_user):
        from apps.loans.services import LoanService
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        result = svc.transition(loan, "under_review", user=admin_user)
        assert result.success is True
        assert result.to_state == "under_review"

    def test_full_workflow(self, loan, admin_user):
        from apps.loans.services import LoanService
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        data = {"approved_amount": 45000, "monthly_instalment": 3750, "instalment_count": 12}
        svc.transition(loan, "validated", user=admin_user, metadata=data)
        svc.transition(loan, "paid", user=admin_user, metadata={"payment_reference": "VIR-001", "paid_amount": 45000})
        loan.refresh_from_db()
        assert loan.workflow_state == "paid"
        assert loan.approved_amount == 45000
        assert loan.monthly_instalment == 3750
        assert loan.instalment_count == 12
        assert loan.paid_at is not None
        assert loan.payment_reference == "VIR-001"

    def test_reject_from_submitted(self, loan, admin_user):
        from apps.loans.services import LoanService
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        result = svc.transition(loan, "rejected", user=admin_user, reason="Insufficient documentation")
        assert result.success is True
        loan.refresh_from_db()
        assert loan.workflow_state == "rejected"
        assert loan.rejection_reason == "Insufficient documentation"
        assert loan.rejected_at is not None

    def test_cancel_from_draft(self, loan, admin_user):
        from apps.loans.services import LoanService
        result = LoanService().transition(loan, "cancelled", user=admin_user)
        assert result.success is True
        loan.refresh_from_db()
        assert loan.workflow_state == "cancelled"

    def test_invalid_transition_raises(self, loan, admin_user):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        with pytest.raises(WorkflowError):
            LoanService().transition(loan, "paid", user=admin_user)

    def test_wrong_role_raises(self, loan, comptable):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        with pytest.raises(WorkflowError):
            LoanService().transition(loan, "submitted", user=comptable)

    def test_transition_logs_created(self, loan, admin_user):
        from apps.loans.services import LoanService
        from shared.workflow.models import WorkflowLog
        LoanService().transition(loan, "submitted", user=admin_user)
        logs = WorkflowLog.objects.filter(object_id=str(loan.pk))
        assert logs.count() == 1
        assert logs.first().from_state == "draft"
        assert logs.first().to_state == "submitted"

    def test_approve_directly_needs_admin(self, loan, gestionnaire):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        svc = LoanService()
        svc.transition(loan, "submitted", user=gestionnaire)
        data = {"approved_amount": 45000}
        with pytest.raises(WorkflowError) as exc:
            svc.transition(loan, "validated", user=gestionnaire, metadata=data)
        assert exc.value.code == "FORBIDDEN_TRANSITION"


# ═══════════════════════════════════════════════════════════
# GUARD TESTS
# ═══════════════════════════════════════════════════════════

class TestGuards:

    def test_approved_amount_required_for_validate(self, loan, admin_user):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        with pytest.raises(WorkflowError):
            svc.transition(loan, "validated", user=admin_user)

    def test_payment_reference_required_for_paid(self, loan, admin_user):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        data = {"approved_amount": 45000, "monthly_instalment": 3750, "instalment_count": 12}
        svc.transition(loan, "validated", user=admin_user, metadata=data)
        with pytest.raises(WorkflowError):
            svc.transition(loan, "paid", user=admin_user)

    def test_rejection_requires_reason(self, loan, admin_user):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        with pytest.raises(WorkflowError):
            svc.transition(loan, "rejected", user=admin_user)

    def test_comptable_can_pay(self, loan, admin_user, comptable):
        from apps.loans.services import LoanService
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        data = {"approved_amount": 45000, "monthly_instalment": 3750, "instalment_count": 12}
        svc.transition(loan, "validated", user=admin_user, metadata=data)
        result = svc.transition(loan, "paid", user=comptable,
                                metadata={"payment_reference": "VIR-002", "paid_amount": 45000})
        assert result.success is True


# ═══════════════════════════════════════════════════════════
# API TESTS
# ═══════════════════════════════════════════════════════════

class TestLoanAPI:

    BASE = "/api/v1/loans/"

    def test_list_loans(self, api, loan, admin_user):
        auth(api, admin_user)
        resp = api.get(self.BASE)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert len(body["results"]) >= 1

    def test_create_loan(self, api, employee, admin_user):
        auth(api, admin_user)
        resp = api.post(self.BASE, {
            "employee": str(employee.id),
            "requested_amount": 75000,
            "reason": "Home renovation",
        }, format="json")
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["workflow_state"] == "draft"
        assert body["data"]["reference"].startswith("PRET-")

    def test_create_loan_requires_amount(self, api, employee, admin_user):
        auth(api, admin_user)
        resp = api.post(self.BASE, {
            "employee": str(employee.id),
            "requested_amount": 0,
            "reason": "Test",
        }, format="json")
        assert resp.status_code == 400

    def test_retrieve_loan(self, api, loan, admin_user):
        auth(api, admin_user)
        resp = api.get(f"{self.BASE}{loan.id}/")
        assert resp.status_code == 200

    def test_delete_loan_draft(self, api, loan, admin_user):
        auth(api, admin_user)
        resp = api.delete(f"{self.BASE}{loan.id}/")
        assert resp.status_code == 200

    def test_delete_loan_submitted_blocked(self, api, loan, admin_user):
        from apps.loans.services import LoanService
        auth(api, admin_user)
        LoanService().transition(loan, "submitted", user=admin_user)
        resp = api.delete(f"{self.BASE}{loan.id}/")
        assert resp.status_code == 400

    def test_api_transition(self, api, loan, admin_user):
        auth(api, admin_user)
        resp = api.post(f"{self.BASE}{loan.id}/transition/", {"to_state": "submitted"}, format="json")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["workflow_state"] == "submitted"

    def test_available_transitions_unauthenticated(self, api, loan):
        resp = api.get(f"{self.BASE}{loan.id}/available-transitions/")
        assert resp.status_code == 401

    def test_available_transitions(self, api, loan, admin_user):
        auth(api, admin_user)
        resp = api.get(f"{self.BASE}{loan.id}/available-transitions/")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) > 0

    def test_statistics(self, api, admin_user):
        auth(api, admin_user)
        resp = api.get(f"{self.BASE}statistics/")
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body["data"]


# ═══════════════════════════════════════════════════════════
# ATTACHMENT & COMMENT TESTS
# ═══════════════════════════════════════════════════════════

class TestAttachmentsAndComments:

    def test_add_comment(self, api, loan, admin_user):
        auth(api, admin_user)
        resp = api.post(f"/api/v1/loans/{loan.id}/comments/", {
            "content": "Vérifier les documents",
            "comment_type": "internal",
        }, format="json")
        assert resp.status_code == 201

    def test_workflow_log_endpoint(self, api, loan, admin_user):
        from apps.loans.services import LoanService
        auth(api, admin_user)
        LoanService().transition(loan, "submitted", user=admin_user)
        resp = api.get(f"/api/v1/loans/{loan.id}/workflow-log/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1


# ═══════════════════════════════════════════════════════════
# SERVICE TESTS
# ═══════════════════════════════════════════════════════════

class TestLoanService:

    def test_search_by_reference(self, loan, admin_user):
        from apps.loans.services import LoanService
        svc = LoanService()
        qs = svc.get_queryset()
        results = svc.search(qs, search_term=loan.reference)
        assert results.count() >= 1

    def test_search_by_employee_name(self, loan, admin_user):
        from apps.loans.services import LoanService
        svc = LoanService()
        qs = svc.get_queryset()
        results = svc.search(qs, search_term="John")
        assert results.count() >= 1

    def test_statistics_counts(self, loan, admin_user, employee):
        from apps.loans.services import LoanService
        svc = LoanService()
        stats = svc.get_statistics()
        assert stats["total"] >= 1
        assert "by_state" in stats
        assert stats["total_requested"] >= 50000

    def test_delete_draft_succeeds(self, loan, admin_user):
        from apps.loans.services import LoanService
        svc = LoanService()
        svc.delete(loan, admin_user)
        loan.refresh_from_db()
        assert loan.is_deleted is True

    def test_delete_submitted_fails(self, loan, admin_user):
        from apps.loans.services import LoanService
        from shared.workflow.engine import WorkflowError
        svc = LoanService()
        svc.transition(loan, "submitted", user=admin_user)
        with pytest.raises(WorkflowError):
            svc.delete(loan, admin_user)
