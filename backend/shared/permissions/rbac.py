"""
============================================================
PERMISSIONS ENGINE — RBAC + ABAC pour applications Django
============================================================
Architecture gouvernementale : rôle granulaire + attributs.

RBAC (Role-Based Access Control) :
    Roles définis → permissions par action → combinaisons OR

ABAC (Attribute-Based Access Control) :
    Règles basées sur attributs de l'objet, de l'utilisateur, du contexte
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class Role:
    """Roles par défaut — chaque projet peut étendre via ENGINE_ROLES."""

    ADMIN = "admin"
    GESTIONNAIRE = "gestionnaire"
    COMPTABLE = "comptable"
    CONSULTANT = "consultant"
    STAFF = [ADMIN, GESTIONNAIRE, COMPTABLE]


def get_configured_roles():
    """Return roles from engine registry."""
    try:
        from shared.registry import registry

        roles = registry.get_roles()
        if roles:
            return roles
    except ImportError:
        pass
    return set(Role.STAFF + [Role.CONSULTANT])


# ═══════════════════════════════════════════════════════════
# P ERMISSIONS DE BASE (RBAC)
# ═══════════════════════════════════════════════════════════


class HasRole(BasePermission):
    """Vérifie si l'utilisateur a un rôle spécifique."""

    allowed_roles = []

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.allowed_roles


class IsAdmin(HasRole):
    allowed_roles = [Role.ADMIN]
    message = "Accès réservé aux administrateurs."


class IsGestionnaire(HasRole):
    allowed_roles = [Role.GESTIONNAIRE]
    message = "Accès réservé aux gestionnaires."


class IsComptable(HasRole):
    allowed_roles = [Role.COMPTABLE]
    message = "Accès réservé aux comptables."


class IsConsultant(HasRole):
    allowed_roles = [Role.CONSULTANT]
    message = "Accès réservé aux consultants."


# ═══════════════════════════════════════════════════════════
# P ERMISSIONS COMBINÉES (OR)
# ═══════════════════════════════════════════════════════════


class HasAnyRole(BasePermission):
    """L'utilisateur doit avoir au moins un des rôles listés."""

    allowed_roles = []

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.allowed_roles


class IsStaff(HasAnyRole):
    allowed_roles = Role.STAFF
    message = "Accès réservé au personnel."


class IsAdminOrGestionnaire(HasAnyRole):
    allowed_roles = [Role.ADMIN, Role.GESTIONNAIRE]
    message = "Accès réservé aux administrateurs et gestionnaires."


class IsAdminOrComptable(HasAnyRole):
    allowed_roles = [Role.ADMIN, Role.COMPTABLE]
    message = "Accès réservé aux administrateurs et comptables."


# ═══════════════════════════════════════════════════════════
# P ERMISSIONS MIXTES (RBAC + HTTP METHOD)
# ═══════════════════════════════════════════════════════════


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == Role.ADMIN


# ═══════════════════════════════════════════════════════════
# P ERMISSIONS SUR OBJET (ABAC)
# ═══════════════════════════════════════════════════════════


class IsOwnerOrAdmin(BasePermission):
    message = "Vous ne pouvez accéder qu'à vos propres données."

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "created_by", None)
        return owner == request.user


class HasObjectAttribute(BasePermission):
    """
    Permission ABAC : vérifie un attribut de l'objet.

    Usage:
        class CanAccessDepartment(HasObjectAttribute):
            attribute = "department_id"
            allowed_values = lambda user: [user.department_id]

    À surcharger dans les sous-classes.
    """

    attribute = ""
    allowed_values = None

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True
        if not self.attribute:
            return True
        val = getattr(obj, self.attribute, None)
        if self.allowed_values:
            allowed = (
                self.allowed_values(request.user)
                if callable(self.allowed_values)
                else self.allowed_values
            )
            return val in allowed
        return True


# ═══════════════════════════════════════════════════════════
# F ACTORY — créer une permission depuis une config
# ═══════════════════════════════════════════════════════════


class DynamicRolePermission(BasePermission):
    """Permission basée sur des rôles définis dynamiquement."""

    allowed_roles = []

    def __init__(self, roles=None):
        if roles is not None:
            self.allowed_roles = roles
        super().__init__()

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.allowed_roles


def role_required(*roles):
    """Factory retournant une classe de permission pour les rôles donnés."""
    return type(
        "DynamicPermission",
        (DynamicRolePermission,),
        {"allowed_roles": list(roles)},
    )
