import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = [pytest.mark.django_db]


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def approval_matrix():
    from django.apps import apps
    ApprovalMatrix = apps.get_model("administration", "ApprovalMatrix")
    Role = apps.get_model("administration", "Role")
    director = Role.objects.get(slug="director")
    manager = Role.objects.get(slug="department_manager")
    matrix = ApprovalMatrix.objects.create(
        module="loan",
        min_amount=Decimal("0"),
        max_amount=Decimal("100000"),
        approval_level=1,
        is_active=True,
    )
    matrix.required_roles.add(manager)
    matrix2 = ApprovalMatrix.objects.create(
        module="loan",
        min_amount=Decimal("100001"),
        max_amount=Decimal("500000"),
        approval_level=2,
        is_active=True,
    )
    matrix2.required_roles.add(director)
    matrix3 = ApprovalMatrix.objects.create(
        module="loan",
        min_amount=Decimal("500001"),
        approval_level=3,
        is_active=True,
    )
    matrix3.required_roles.add(director)
    return matrix, matrix2, matrix3


# ── get_approval_matrix_for_amount ────────────────────────

class TestGetApprovalMatrixForAmount:

    def test_low_amount_matches_level_1(self, approval_matrix):
        from apps.administration.services import get_approval_matrix_for_amount
        result = get_approval_matrix_for_amount("loan", Decimal("50000"))
        assert result is not None
        assert result.approval_level == 1

    def test_mid_amount_matches_level_2(self, approval_matrix):
        from apps.administration.services import get_approval_matrix_for_amount
        result = get_approval_matrix_for_amount("loan", Decimal("200000"))
        assert result is not None
        assert result.approval_level == 2

    def test_high_amount_matches_level_3(self, approval_matrix):
        from apps.administration.services import get_approval_matrix_for_amount
        result = get_approval_matrix_for_amount("loan", Decimal("999999"))
        assert result is not None
        assert result.approval_level == 3

    def test_boundary_exact_match(self, approval_matrix):
        from apps.administration.services import get_approval_matrix_for_amount
        result = get_approval_matrix_for_amount("loan", Decimal("100001"))
        assert result is not None
        assert result.approval_level == 2

    def test_no_matching_module_returns_none(self, approval_matrix):
        from apps.administration.services import get_approval_matrix_for_amount
        result = get_approval_matrix_for_amount("nonexistent", Decimal("50000"))
        assert result is None

    def test_inactive_rule_not_returned(self, approval_matrix):
        from apps.administration.services import get_approval_matrix_for_amount
        from django.apps import apps
        ApprovalMatrix = apps.get_model("administration", "ApprovalMatrix")
        inactive = ApprovalMatrix.objects.create(
            module="loan",
            min_amount=Decimal("0"),
            max_amount=Decimal("100000"),
            approval_level=1,
            is_active=False,
        )
        result = get_approval_matrix_for_amount("loan", Decimal("50000"))
        assert result is not None
        assert result.id != inactive.id


# ── requires_director_approval ────────────────────────────

class TestRequiresDirectorApproval:

    def test_level_1_does_not_require_director(self, approval_matrix):
        from apps.administration.services import requires_director_approval
        assert requires_director_approval("loan", Decimal("50000")) is False

    def test_level_2_requires_director(self, approval_matrix):
        from apps.administration.services import requires_director_approval
        assert requires_director_approval("loan", Decimal("200000")) is True

    def test_level_3_requires_director(self, approval_matrix):
        from apps.administration.services import requires_director_approval
        assert requires_director_approval("loan", Decimal("999999")) is True

    def test_no_matrix_returns_false(self, approval_matrix):
        from apps.administration.services import requires_director_approval
        assert requires_director_approval("nonexistent", Decimal("50000")) is False


# ── get_escalation_threshold ──────────────────────────────

class TestGetEscalationThreshold:

    def test_returns_lowest_level_2_min_amount(self, approval_matrix):
        from apps.administration.services import get_escalation_threshold
        result = get_escalation_threshold("loan")
        assert result == Decimal("100001")

    def test_no_level_2_returns_none(self, approval_matrix):
        from apps.administration.services import get_escalation_threshold
        from django.apps import apps
        ApprovalMatrix = apps.get_model("administration", "ApprovalMatrix")
        ApprovalMatrix.objects.filter(approval_level__gte=2).delete()
        result = get_escalation_threshold("loan")
        assert result is None

    def test_inactive_level_2_not_considered(self):
        from apps.administration.services import get_escalation_threshold
        from django.apps import apps
        ApprovalMatrix = apps.get_model("administration", "ApprovalMatrix")
        ApprovalMatrix.objects.create(
            module="loan",
            min_amount=Decimal("50000"),
            approval_level=2,
            is_active=False,
        )
        result = get_escalation_threshold("loan")
        assert result is None


# ── get_required_roles_for_amount ─────────────────────────

class TestGetRequiredRolesForAmount:

    def test_returns_roles_for_matching_level(self, approval_matrix):
        from apps.administration.services import get_required_roles_for_amount
        roles = get_required_roles_for_amount("loan", Decimal("50000"))
        assert len(roles) == 1
        assert roles[0].slug == "department_manager"

    def test_returns_director_for_high_amount(self, approval_matrix):
        from apps.administration.services import get_required_roles_for_amount
        roles = get_required_roles_for_amount("loan", Decimal("200000"))
        assert len(roles) >= 1
        assert any(r.slug == "director" for r in roles)

    def test_no_matrix_returns_empty(self, approval_matrix):
        from apps.administration.services import get_required_roles_for_amount
        assert get_required_roles_for_amount("nonexistent", Decimal("50000")) == []
