import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = [pytest.mark.django_db]


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@t.dz", password="P@ss123!",
        first_name="Admin", last_name="Test", role="admin",
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email="user@t.dz", password="P@ss123!",
        first_name="User", last_name="Test", role="gestionnaire",
    )


@pytest.fixture
def director_user(db):
    return User.objects.create_user(
        email="director@t.dz", password="P@ss123!",
        first_name="Director", last_name="Test", role="director",
    )


# ── user_has_permission ───────────────────────────────────

class TestUserHasPermission:

    def test_admin_always_has_permission(self, admin_user):
        from core.permissions import user_has_permission
        assert user_has_permission(admin_user, "nonexistent.permission") is True

    def test_unauthenticated_returns_false(self):
        from core.permissions import user_has_permission
        anonymous = type("obj", (), {"is_authenticated": False})()
        assert user_has_permission(anonymous, "loan.view") is False

    def test_user_with_permission_returns_true(self, normal_user):
        from core.permissions import user_has_permission
        from django.apps import apps
        Permission = apps.get_model("administration", "Permission")
        RolePermission = apps.get_model("administration", "RolePermission")
        Role = apps.get_model("administration", "Role")
        perm = Permission.objects.get(codename="loan.view")
        role = Role.objects.get(slug="gestionnaire")
        RolePermission.objects.get_or_create(role=role, permission=perm)
        assert user_has_permission(normal_user, "loan.view") is True

    def test_user_without_permission_returns_false(self, normal_user):
        from core.permissions import user_has_permission
        assert user_has_permission(normal_user, "admin.manage_roles") is False

    def test_superuser_always_has_permission(self, db):
        su = User.objects.create_superuser(
            email="su@t.dz", password="P@ss123!",
            role="admin",
        )
        from core.permissions import user_has_permission
        assert user_has_permission(su, "anything") is True


# ── user_has_roles ────────────────────────────────────────

class TestUserHasRoles:

    def test_matches_primary_role(self, normal_user):
        from core.permissions import user_has_roles
        assert user_has_roles(normal_user, "gestionnaire", "admin") is True

    def test_no_match_returns_false(self, normal_user):
        from core.permissions import user_has_roles
        assert user_has_roles(normal_user, "director", "comptable") is False

    def test_matches_extra_role(self, normal_user):
        from core.permissions import user_has_roles
        from django.apps import apps
        UserRoleAssignment = apps.get_model("administration", "UserRoleAssignment")
        Role = apps.get_model("administration", "Role")
        director = Role.objects.get(slug="director")
        UserRoleAssignment.objects.create(
            user=normal_user, role=director,
            assigned_by=normal_user,
        )
        assert user_has_roles(normal_user, "director") is True

    def test_unauthenticated_returns_false(self):
        from core.permissions import user_has_roles
        anonymous = type("obj", (), {"is_authenticated": False})()
        assert user_has_roles(anonymous, "gestionnaire") is False

    def test_inactive_extra_role_not_counted(self, normal_user):
        from core.permissions import user_has_roles
        from django.apps import apps
        UserRoleAssignment = apps.get_model("administration", "UserRoleAssignment")
        Role = apps.get_model("administration", "Role")
        director = Role.objects.get(slug="director")
        UserRoleAssignment.objects.create(
            user=normal_user, role=director,
            assigned_by=normal_user, is_active=False,
        )
        assert user_has_roles(normal_user, "director") is False


# ── user_can_transition ──────────────────────────────────

class TestUserCanTransition:

    @pytest.fixture
    def workflow_perm(self, normal_user):
        from django.apps import apps
        Role = apps.get_model("administration", "Role")
        WorkflowPermission = apps.get_model("administration", "WorkflowPermission")
        role = Role.objects.get(slug="gestionnaire")
        wp = WorkflowPermission.objects.create(
            app_label="loans", model_name="loan",
            from_state="submitted", to_state="under_review",
            role=role,
        )
        return wp

    def test_admin_can_always_transition(self, admin_user):
        from core.permissions import user_can_transition
        assert user_can_transition(admin_user, "loans", "loan",
                                   "submitted", "under_review") is True

    def test_user_with_permission_can_transition(self, normal_user, workflow_perm):
        from core.permissions import user_can_transition
        assert user_can_transition(normal_user, "loans", "loan",
                                   "submitted", "under_review") is True

    def test_user_without_permission_cannot_transition(self, normal_user):
        from core.permissions import user_can_transition
        assert user_can_transition(normal_user, "loans", "loan",
                                   "validated", "paid") is False

    def test_unauthenticated_returns_false(self, workflow_perm):
        from core.permissions import user_can_transition
        anonymous = type("obj", (), {"is_authenticated": False})()
        assert user_can_transition(anonymous, "loans", "loan",
                                   "submitted", "under_review") is False


# ── HasPermission DRF class ───────────────────────────────

class TestHasPermissionDRF:

    def test_admin_always_allowed(self, admin_user):
        from core.permissions import HasPermission
        perm = HasPermission(codename="anything")
        request = type("req", (), {"user": admin_user, "method": "POST"})()
        assert perm.has_permission(request, None) is True

    def test_authenticated_without_codename_allowed(self, normal_user):
        from core.permissions import HasPermission
        perm = HasPermission()
        request = type("req", (), {"user": normal_user, "method": "GET"})()
        assert perm.has_permission(request, None) is True

    def test_unauthenticated_denied(self):
        from core.permissions import HasPermission
        perm = HasPermission(codename="loan.view")
        anon = type("obj", (), {"is_authenticated": False})()
        request = type("req", (), {"user": anon, "method": "GET"})()
        assert perm.has_permission(request, None) is False


# ── HasRoles DRF class ────────────────────────────────────

class TestHasRolesDRF:

    def test_matching_role_allowed(self, normal_user):
        from core.permissions import HasRoles
        perm = HasRoles("gestionnaire")
        request = type("req", (), {"user": normal_user, "method": "POST"})()
        assert perm.has_permission(request, None) is True

    def test_non_matching_role_denied(self, normal_user):
        from core.permissions import HasRoles
        perm = HasRoles("director")
        request = type("req", (), {"user": normal_user, "method": "GET"})()
        assert perm.has_permission(request, None) is False

    def test_unauthenticated_denied(self):
        from core.permissions import HasRoles
        perm = HasRoles("gestionnaire")
        anon = type("obj", (), {"is_authenticated": False})()
        request = type("req", (), {"user": anon, "method": "GET"})()
        assert perm.has_permission(request, None) is False
