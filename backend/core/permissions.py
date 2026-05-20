"""
============================================================
PERMISSIONS RBAC — Système de permissions par rôle
============================================================
4 rôles : admin, gestionnaire, comptable, consultant

Utilisation dans les vues :
    permission_classes = [IsAuthenticated, IsAdmin]
    permission_classes = [IsAuthenticated, IsGestionnaireOrAdmin]
"""
from rest_framework.permissions import BasePermission

# ── Constantes des rôles ──────────────────────────────────
class Role:
    ADMIN = "admin"
    GESTIONNAIRE = "gestionnaire"
    COMPTABLE = "comptable"
    CONSULTANT = "consultant"

    ALL = [ADMIN, GESTIONNAIRE, COMPTABLE, CONSULTANT]
    STAFF = [ADMIN, GESTIONNAIRE, COMPTABLE]


# ── Permissions de base par rôle ──────────────────────────
class IsAdmin(BasePermission):
    """Réservé aux administrateurs système."""
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsGestionnaire(BasePermission):
    """Réservé aux gestionnaires RH."""
    message = "Accès réservé aux gestionnaires."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.GESTIONNAIRE
        )


class IsComptable(BasePermission):
    """Réservé aux comptables/financiers."""
    message = "Accès réservé aux comptables."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.COMPTABLE
        )


class IsConsultant(BasePermission):
    """Accès en lecture seule pour les consultants."""
    message = "Accès réservé aux consultants."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.CONSULTANT
        )


# ── Permissions combinées (OR logic) ─────────────────────
class IsAdminOrGestionnaire(BasePermission):
    """Admin ou Gestionnaire."""
    message = "Accès réservé aux administrateurs et gestionnaires."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [Role.ADMIN, Role.GESTIONNAIRE]
        )


class IsAdminOrComptable(BasePermission):
    """Admin ou Comptable."""
    message = "Accès réservé aux administrateurs et comptables."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [Role.ADMIN, Role.COMPTABLE]
        )


class IsStaff(BasePermission):
    """Tout utilisateur avec un rôle actif (pas consultant)."""
    message = "Accès réservé au personnel."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in Role.STAFF
        )


class IsReadOnly(BasePermission):
    """Autorise uniquement les méthodes GET, HEAD, OPTIONS."""
    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")


# ── Permission mixte : rôle + lecture seule ───────────────
class IsAdminOrReadOnly(BasePermission):
    """Admin pour écriture, tous les authentifiés pour lecture."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.role == Role.ADMIN


# ── Permission sur l'objet ────────────────────────────────
class IsOwnerOrAdmin(BasePermission):
    """
    L'utilisateur peut accéder à son propre objet.
    L'admin peut accéder à tous les objets.
    Requiert que l'objet ait un attribut `created_by` ou `user`.
    """
    message = "Vous ne pouvez accéder qu'à vos propres données."

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True
        # Support pour des modèles avec user ou created_by
        owner = getattr(obj, "user", None) or getattr(obj, "created_by", None)
        return owner == request.user
