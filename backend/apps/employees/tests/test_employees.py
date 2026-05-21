"""
============================================================
EMPLOYEE TESTS — Tests unitaires et d'intégration
============================================================
Couverture : modèles, services, API endpoints, permissions.
"""

from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.dz",
        password="AdminPass123!",
        first_name="Admin",
        last_name="Test",
        role="admin",
    )


@pytest.fixture
def gestionnaire_user(db):
    return User.objects.create_user(
        email="gest@test.dz",
        password="GestPass123!",
        first_name="Gestionnaire",
        last_name="Test",
        role="gestionnaire",
    )


@pytest.fixture
def consultant_user(db):
    return User.objects.create_user(
        email="consult@test.dz",
        password="ConsultPass123!",
        first_name="Consultant",
        last_name="Test",
        role="consultant",
    )


@pytest.fixture
def department(db, admin_user):
    from apps.departments.models import Department

    return Department.objects.create(
        code="RH",
        name="Ressources Humaines",
        created_by=admin_user,
    )


@pytest.fixture
def employee(db, department, admin_user):
    from apps.employees.models import Employee

    return Employee.objects.create(
        first_name="Ahmed",
        last_name="Benali",
        gender="M",
        date_of_birth=date(1985, 6, 15),
        department=department,
        job_title="Ingénieur",
        contract_type="cdi",
        date_hired=date(2010, 3, 1),
        status="active",
        created_by=admin_user,
    )


@pytest.fixture
def auth_admin(api_client, admin_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def auth_consultant(api_client, consultant_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(consultant_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


# ══════════════════════════════════════════════════════════
# TESTS MODÈLES
# ══════════════════════════════════════════════════════════
class TestEmployeeModel:

    def test_full_name(self, employee):
        assert employee.get_full_name() == "Ahmed Benali"

    def test_age_calculation(self, employee):
        today = date.today()
        expected_age = today.year - 1985 - ((today.month, today.day) < (6, 15))
        assert employee.age == expected_age

    def test_seniority_years(self, employee):
        """L'ancienneté doit être positive et calculée depuis date_hired."""
        assert employee.seniority_years > 0
        assert employee.seniority_years > 14  # embauché en 2010

    def test_seniority_label(self, employee):
        label = employee.seniority_label
        assert "an" in label  # "14 ans" ou similaire

    def test_matricule_auto_generated(self, employee):
        assert employee.matricule.startswith("MAT-")
        year = str(date.today().year)
        assert year in employee.matricule

    def test_matricule_unique(self, db, department, admin_user):
        from apps.employees.models import Employee

        e1 = Employee.objects.create(
            first_name="A",
            last_name="B",
            gender="M",
            date_of_birth=date(1990, 1, 1),
            department=department,
            job_title="Dev",
            date_hired=date(2020, 1, 1),
        )
        e2 = Employee.objects.create(
            first_name="C",
            last_name="D",
            gender="F",
            date_of_birth=date(1992, 1, 1),
            department=department,
            job_title="Dev",
            date_hired=date(2021, 1, 1),
        )
        assert e1.matricule != e2.matricule

    def test_soft_delete(self, employee):
        employee.soft_delete()
        assert employee.is_deleted is True
        assert employee.deleted_at is not None
        # Ne doit plus apparaître dans le manager par défaut
        from apps.employees.models import Employee

        assert not Employee.objects.filter(pk=employee.pk).exists()
        # Mais visible via all_objects
        assert Employee.all_objects.filter(pk=employee.pk).exists()

    def test_photo_url_none_when_no_photo(self, employee):
        assert employee.photo_url is None

    def test_beneficiaries_count_zero_initially(self, employee):
        assert employee.beneficiaries_count == 0


# ══════════════════════════════════════════════════════════
# TESTS SERVICE
# ══════════════════════════════════════════════════════════
class TestEmployeeService:

    def test_create_employee(self, db, department, admin_user):
        from apps.employees.services import EmployeeService

        service = EmployeeService()
        data = {
            "first_name": "Fatima",
            "last_name": "Kaci",
            "gender": "F",
            "date_of_birth": date(1990, 3, 20),
            "department": department,
            "job_title": "Comptable",
            "contract_type": "cdi",
            "date_hired": date(2018, 1, 15),
            "status": "active",
        }
        emp = service.create(data, user=admin_user)
        assert emp.pk is not None
        assert emp.matricule.startswith("MAT-")
        assert emp.created_by == admin_user

    def test_search_by_name(self, db, employee):
        from apps.employees.services import EmployeeService

        service = EmployeeService()
        qs = service.search(service.get_queryset(), search_term="Ahmed")
        assert employee in qs

    def test_search_by_status(self, db, employee):
        from apps.employees.services import EmployeeService

        service = EmployeeService()
        qs = service.search(service.get_queryset(), status="active")
        assert employee in qs
        qs_inactive = service.search(service.get_queryset(), status="inactive")
        assert employee not in qs_inactive

    def test_statistics_structure(self, db, employee):
        from apps.employees.services import EmployeeService

        stats = EmployeeService().get_statistics()
        assert "total" in stats
        assert "by_status" in stats
        assert "by_department" in stats
        assert "active_count" in stats
        assert stats["total"] >= 1

    def test_update_employee(self, db, employee, admin_user):
        from apps.employees.services import EmployeeService

        service = EmployeeService()
        updated = service.update(employee, {"job_title": "Senior Ingénieur"}, user=admin_user)
        assert updated.job_title == "Senior Ingénieur"
        assert updated.updated_by == admin_user

    def test_soft_delete_via_service(self, db, employee, admin_user):
        from apps.employees.models import Employee
        from apps.employees.services import EmployeeService

        service = EmployeeService()
        service.delete(employee, user=admin_user)
        assert not Employee.objects.filter(pk=employee.pk).exists()


# ══════════════════════════════════════════════════════════
# TESTS API
# ══════════════════════════════════════════════════════════
class TestEmployeeAPI:

    def test_list_requires_auth(self, api_client):
        resp = api_client.get("/api/v1/employees/")
        assert resp.status_code == 401

    def test_list_returns_paginated(self, auth_admin, employee):
        resp = auth_admin.get("/api/v1/employees/")
        assert resp.status_code == 200
        data = resp.json()
        assert "pagination" in data
        assert "results" in data
        assert data["pagination"]["count"] >= 1

    def test_retrieve_employee(self, auth_admin, employee):
        resp = auth_admin.get(f"/api/v1/employees/{employee.id}/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["matricule"] == employee.matricule
        assert data["first_name"] == "Ahmed"
        assert "age" in data
        assert "seniority_years" in data
        assert "beneficiaries" in data

    def test_create_employee(self, auth_admin, department):
        payload = {
            "first_name": "Nassim",
            "last_name": "Hadj",
            "gender": "M",
            "date_of_birth": "1988-07-12",
            "department": str(department.id),
            "job_title": "Analyste",
            "contract_type": "cdi",
            "date_hired": "2019-04-01",
            "status": "active",
        }
        resp = auth_admin.post("/api/v1/employees/", data=payload, format="json")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["first_name"] == "Nassim"
        assert data["matricule"].startswith("MAT-")

    def test_update_employee_patch(self, auth_admin, employee):
        resp = auth_admin.patch(
            f"/api/v1/employees/{employee.id}/",
            data={"job_title": "Lead Ingénieur"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["job_title"] == "Lead Ingénieur"

    def test_consultant_cannot_create(self, auth_consultant, department):
        """Les consultants n'ont pas le droit de créer des employés."""
        payload = {
            "first_name": "X",
            "last_name": "Y",
            "gender": "M",
            "date_of_birth": "1990-01-01",
            "department": str(department.id),
            "job_title": "Dev",
            "contract_type": "cdi",
            "date_hired": "2020-01-01",
            "status": "active",
        }
        resp = auth_consultant.post("/api/v1/employees/", data=payload, format="json")
        assert resp.status_code == 403

    def test_search_filter(self, auth_admin, employee):
        resp = auth_admin.get("/api/v1/employees/?search=Ahmed")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert any(e["first_name"] == "Ahmed" for e in results)

    def test_statistics_endpoint(self, auth_admin, employee):
        resp = auth_admin.get("/api/v1/employees/statistics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total" in data
        assert data["total"] >= 1

    def test_history_endpoint(self, auth_admin, employee):
        resp = auth_admin.get(f"/api/v1/employees/{employee.id}/history/")
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_change_status(self, auth_admin, employee):
        resp = auth_admin.post(
            f"/api/v1/employees/{employee.id}/change-status/",
            data={"status": "inactive", "reason": "Congé sans solde"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "inactive"

    def test_date_validation_future_hired(self, auth_admin, department):
        """La date d'embauche dans le futur doit être rejetée."""
        future = (date.today() + timedelta(days=30)).isoformat()
        payload = {
            "first_name": "X",
            "last_name": "Y",
            "gender": "M",
            "date_of_birth": "1990-01-01",
            "department": str(department.id),
            "job_title": "Dev",
            "contract_type": "cdi",
            "date_hired": future,
            "status": "active",
        }
        resp = auth_admin.post("/api/v1/employees/", data=payload, format="json")
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════
# TESTS BÉNÉFICIAIRES
# ══════════════════════════════════════════════════════════
class TestBeneficiaryModel:

    def test_child_under_18_eligible(self, db, employee, admin_user):
        from apps.beneficiaries.models import Beneficiary

        child = Beneficiary.objects.create(
            employee=employee,
            first_name="Ali",
            last_name="Benali",
            gender="M",
            date_of_birth=date(2015, 1, 1),
            relationship="child",
            created_by=admin_user,
        )
        eligible, reason = child.check_eligibility()
        assert eligible is True

    def test_child_over_25_not_eligible(self, db, employee, admin_user):
        from apps.beneficiaries.models import Beneficiary

        child = Beneficiary.objects.create(
            employee=employee,
            first_name="Youcef",
            last_name="Benali",
            gender="M",
            date_of_birth=date(1990, 1, 1),  # > 25 ans
            relationship="child",
            created_by=admin_user,
        )
        eligible, reason = child.check_eligibility()
        assert eligible is False
        assert "25" in reason or "non étudiant" in reason

    def test_spouse_always_eligible(self, db, employee, admin_user):
        from apps.beneficiaries.models import Beneficiary

        spouse = Beneficiary.objects.create(
            employee=employee,
            first_name="Sara",
            last_name="Kaci",
            gender="F",
            date_of_birth=date(1987, 3, 15),
            relationship="spouse",
            created_by=admin_user,
        )
        eligible, reason = spouse.check_eligibility()
        assert eligible is True

    def test_handicapped_child_always_eligible(self, db, employee, admin_user):
        from apps.beneficiaries.models import Beneficiary

        child = Beneficiary.objects.create(
            employee=employee,
            first_name="Amine",
            last_name="Benali",
            gender="M",
            date_of_birth=date(1988, 5, 10),  # > 25 ans
            relationship="child",
            is_handicapped=True,
            created_by=admin_user,
        )
        eligible, reason = child.check_eligibility()
        assert eligible is True
