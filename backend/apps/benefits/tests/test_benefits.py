"""Benefits tests — workflow et API."""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────
@pytest.fixture
def admin_user(db):
    return User.objects.create_user(email="admin@t.dz", password="P@ss123!", first_name="A", last_name="D", role="admin")

@pytest.fixture
def gestionnaire(db):
    return User.objects.create_user(email="gest@t.dz", password="P@ss123!", first_name="G", last_name="D", role="gestionnaire")

@pytest.fixture
def comptable(db):
    return User.objects.create_user(email="comp@t.dz", password="P@ss123!", first_name="C", last_name="D", role="comptable")

@pytest.fixture
def department(db, admin_user):
    from apps.departments.models import Department
    return Department.objects.create(code="TEST", name="Test", created_by=admin_user)

@pytest.fixture
def employee(db, department, admin_user):
    from apps.employees.models import Employee
    return Employee.objects.create(
        first_name="Emp", last_name="Test", gender="M",
        date_of_birth=date(1985,1,1), department=department,
        job_title="Dev", date_hired=date(2010,1,1), status="active",
        created_by=admin_user,
    )

@pytest.fixture
def benefit_type(db, admin_user):
    from apps.benefits.models import BenefitType
    return BenefitType.objects.create(
        code="MED01", name="Soin médical", category="medical",
        max_amount=100000, min_seniority_years=1,
        target_processing_days=5, created_by=admin_user,
    )

@pytest.fixture
def benefit(db, employee, benefit_type, admin_user):
    from apps.benefits.models import Benefit
    return Benefit.objects.create(
        employee=employee, benefit_type=benefit_type,
        title="Consultation spécialiste", requested_amount=45000,
        priority="normal", created_by=admin_user,
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
# TESTS WORKFLOW ENGINE
# ═══════════════════════════════════════════════════════════
class TestWorkflowEngine:

    def test_initial_state_is_draft(self, benefit):
        assert benefit.workflow_state == "draft"

    def test_state_label(self, benefit):
        assert benefit.workflow_state_label == "Brouillon"

    def test_is_not_final_in_draft(self, benefit):
        assert benefit.is_final is False

    def test_paid_is_final(self, benefit, admin_user):
        benefit.workflow_state = "paid"
        benefit.save(update_fields=["workflow_state"])
        assert benefit.is_final is True

    def test_transition_draft_to_submitted(self, benefit, admin_user):
        from apps.benefits.services import BenefitService
        result = BenefitService().transition(benefit, "submitted", user=admin_user)
        assert result.success is True
        assert result.to_state == "submitted"
        benefit.refresh_from_db()
        assert benefit.workflow_state == "submitted"
        assert benefit.submitted_at is not None

    def test_transition_logs_created(self, benefit, admin_user):
        from apps.benefits.services import BenefitService
        from shared.workflow.models import WorkflowLog
        BenefitService().transition(benefit, "submitted", user=admin_user)
        logs = WorkflowLog.objects.filter(object_id=str(benefit.pk))
        assert logs.count() == 1
        assert logs.first().from_state == "draft"
        assert logs.first().to_state   == "submitted"

    def test_invalid_transition_raises(self, benefit, admin_user):
        from shared.workflow.engine import WorkflowError
        from apps.benefits.services import BenefitService
        with pytest.raises(WorkflowError):
            BenefitService().transition(benefit, "paid", user=admin_user)

    def test_wrong_role_raises(self, benefit, comptable):
        from shared.workflow.engine import WorkflowError
        from apps.benefits.services import BenefitService
        with pytest.raises(WorkflowError) as exc_info:
            BenefitService().transition(benefit, "submitted", user=comptable)
        assert "FORBIDDEN" in exc_info.value.code

    def test_rejection_requires_reason(self, benefit, gestionnaire):
        from shared.workflow.engine import WorkflowError
        from apps.benefits.services import BenefitService
        svc = BenefitService()
        svc.transition(benefit, "submitted", user=gestionnaire)
        with pytest.raises(WorkflowError) as exc_info:
            svc.transition(benefit, "rejected", user=gestionnaire, reason="")
        assert "REASON_REQUIRED" in exc_info.value.code

    def test_rejection_with_reason_succeeds(self, benefit, gestionnaire):
        from apps.benefits.services import BenefitService
        svc = BenefitService()
        svc.transition(benefit, "submitted", user=gestionnaire)
        result = svc.transition(benefit, "rejected", user=gestionnaire, reason="Document manquant")
        assert result.success is True
        benefit.refresh_from_db()
        assert benefit.workflow_state  == "rejected"
        assert benefit.rejection_reason == "Document manquant"

    def test_full_workflow_cycle(self, benefit, admin_user, gestionnaire, comptable):
        """Test du cycle complet : draft → submitted → under_review → validated → paid."""
        from apps.benefits.services import BenefitService
        svc = BenefitService()
        # Soumission
        svc.transition(benefit, "submitted",    user=gestionnaire)
        svc.transition(benefit, "under_review", user=gestionnaire)
        svc.transition(benefit, "validated",    user=gestionnaire,
                       metadata={"approved_amount": 45000})
        svc.transition(benefit, "paid",         user=comptable,
                       metadata={"payment_reference": "VIR-2024-001", "paid_amount": 45000})
        benefit.refresh_from_db()
        assert benefit.workflow_state  == "paid"
        assert benefit.is_final        is True
        assert benefit.payment_reference == "VIR-2024-001"
        assert benefit.validated_at    is not None
        assert benefit.paid_at         is not None

        # 5 logs : draft→submitted, submitted→under_review, …→validated, …→paid
        from shared.workflow.models import WorkflowLog
        assert WorkflowLog.objects.filter(object_id=str(benefit.pk)).count() == 4

    def test_payment_requires_reference(self, benefit, admin_user, comptable):
        from shared.workflow.engine import WorkflowError
        from apps.benefits.services import BenefitService
        svc = BenefitService()
        svc.transition(benefit, "submitted",    user=admin_user)
        svc.transition(benefit, "under_review", user=admin_user)
        svc.transition(benefit, "validated",    user=admin_user, metadata={"approved_amount": 45000})
        with pytest.raises(WorkflowError):
            svc.transition(benefit, "paid", user=comptable, metadata={})

    def test_duplicate_check_guard(self, db, employee, benefit_type, admin_user, gestionnaire):
        """Un employé ne peut pas avoir deux demandes actives du même type."""
        from apps.benefits.models import Benefit
        from apps.benefits.services import BenefitService
        from shared.workflow.engine import WorkflowError
        svc = BenefitService()

        b1 = Benefit.objects.create(
            employee=employee, benefit_type=benefit_type,
            title="Demande 1", requested_amount=10000, created_by=admin_user,
        )
        svc.transition(b1, "submitted", user=gestionnaire)

        b2 = Benefit.objects.create(
            employee=employee, benefit_type=benefit_type,
            title="Demande 2", requested_amount=20000, created_by=admin_user,
        )
        with pytest.raises(WorkflowError):
            svc.transition(b2, "submitted", user=gestionnaire)

    def test_on_hold_and_resubmit(self, benefit, gestionnaire):
        from apps.benefits.services import BenefitService
        svc = BenefitService()
        svc.transition(benefit, "submitted",  user=gestionnaire)
        svc.transition(benefit, "on_hold",    user=gestionnaire, reason="Document manquant")
        benefit.refresh_from_db()
        assert benefit.workflow_state == "on_hold"
        svc.transition(benefit, "submitted",  user=gestionnaire)
        benefit.refresh_from_db()
        assert benefit.workflow_state == "submitted"

    def test_amount_limit_guard(self, db, employee, admin_user, gestionnaire):
        from apps.benefits.models import Benefit, BenefitType
        from apps.benefits.services import BenefitService
        from shared.workflow.engine import WorkflowError
        btype = BenefitType.objects.create(
            code="LIM01", name="Test limité", category="aid",
            max_amount=10000, created_by=admin_user,
        )
        b = Benefit.objects.create(
            employee=employee, benefit_type=btype,
            title="Dépasse le plafond", requested_amount=50000,
            created_by=admin_user,
        )
        with pytest.raises(WorkflowError):
            BenefitService().transition(b, "submitted", user=gestionnaire)

    def test_can_transition_check(self, benefit, admin_user):
        from shared.workflow.engine import WorkflowEngine
        from apps.benefits.workflow import benefit_workflow
        eng = WorkflowEngine(benefit_workflow)
        can, msg = eng.can_transition(benefit, "submitted", actor=admin_user)
        assert can is True
        can2, msg2 = eng.can_transition(benefit, "paid", actor=admin_user)
        assert can2 is False

    def test_get_available_transitions_for_role(self, benefit, gestionnaire):
        transitions = benefit.get_available_transitions(role="gestionnaire")
        states      = [t.to_state for t in transitions]
        assert "submitted" in states
        assert "paid" not in states  # comptable seulement


# ═══════════════════════════════════════════════════════════
# TESTS API
# ═══════════════════════════════════════════════════════════
class TestBenefitAPI:

    def test_create_benefit(self, api, admin_user, employee, benefit_type):
        client = auth(api, admin_user)
        resp = client.post("/api/v1/benefits/", {
            "employee": str(employee.id),
            "benefit_type": str(benefit_type.id),
            "title": "Consultation ORL",
            "requested_amount": "30000.00",
            "priority": "normal",
        }, format="json")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["workflow_state"] == "draft"
        assert data["reference"].startswith("PREST-")

    def test_transition_via_api(self, api, admin_user, benefit):
        client = auth(api, admin_user)
        resp = client.post(f"/api/v1/benefits/{benefit.id}/transition/",
                           {"to_state": "submitted"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["to_state"] == "submitted"

    def test_invalid_transition_returns_400(self, api, admin_user, benefit):
        client = auth(api, admin_user)
        resp = client.post(f"/api/v1/benefits/{benefit.id}/transition/",
                           {"to_state": "paid"}, format="json")
        assert resp.status_code == 400
        data = resp.json()
        assert data["status"] == "error"

    def test_workflow_log_endpoint(self, api, admin_user, benefit):
        from apps.benefits.services import BenefitService
        BenefitService().transition(benefit, "submitted", user=admin_user)
        client = auth(api, admin_user)
        resp = client.get(f"/api/v1/benefits/{benefit.id}/workflow-log/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    def test_available_transitions_endpoint(self, api, gestionnaire, benefit):
        client = auth(api, gestionnaire)
        resp = client.get(f"/api/v1/benefits/{benefit.id}/available-transitions/")
        assert resp.status_code == 200
        transitions = resp.json()["data"]
        states = [t["to_state"] for t in transitions]
        assert "submitted"  in states
        assert "paid"       not in states

    def test_statistics_endpoint(self, api, admin_user, benefit):
        client = auth(api, admin_user)
        resp = client.get("/api/v1/benefits/statistics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total" in data
        assert "by_state" in data
        assert "total_requested" in data

    def test_unauthenticated_returns_401(self, api, benefit):
        resp = api.get("/api/v1/benefits/")
        assert resp.status_code == 401

    def test_full_api_cycle(self, api, admin_user, gestionnaire, comptable, employee, benefit_type):
        """Test du cycle complet via l'API."""
        g_client = auth(api, gestionnaire)
        c_client = auth(api, comptable)
        a_client = auth(api, admin_user)

        # Création
        r = g_client.post("/api/v1/benefits/", {
            "employee": str(employee.id), "benefit_type": str(benefit_type.id),
            "title": "Test cycle complet", "requested_amount": "50000.00", "priority": "normal",
        }, format="json")
        assert r.status_code == 201
        bid = r.json()["data"]["id"]

        # Soumettre
        r = g_client.post(f"/api/v1/benefits/{bid}/transition/", {"to_state":"submitted"}, format="json")
        assert r.status_code == 200

        # Prendre en charge
        r = g_client.post(f"/api/v1/benefits/{bid}/transition/", {"to_state":"under_review"}, format="json")
        assert r.status_code == 200

        # Valider
        r = g_client.post(f"/api/v1/benefits/{bid}/transition/",
                          {"to_state":"validated","approved_amount":50000}, format="json")
        assert r.status_code == 200

        # Payer (comptable)
        r = c_client.post(f"/api/v1/benefits/{bid}/transition/",
                          {"to_state":"paid","payment_reference":"VIR-TEST-001","paid_amount":50000}, format="json")
        assert r.status_code == 200

        # Vérification finale
        r = a_client.get(f"/api/v1/benefits/{bid}/")
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["workflow_state"]    == "paid"
        assert d["payment_reference"] == "VIR-TEST-001"
