import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel

User = get_user_model()


# =========================================================================
# SYSTEM PARAMETERS — Configuration clé/valeur modifiable à l'exécution
# =========================================================================


class SystemParameter(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True, verbose_name=_("Clé"))
    value = models.TextField(verbose_name=_("Valeur"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="system_parameter_updates", verbose_name=_("Mis à jour par"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Mis à jour le"))

    class Meta:
        verbose_name = _("Paramètre système")
        verbose_name_plural = _("Paramètres système")
        ordering = ["key"]

    def __str__(self):
        return self.key


# =========================================================================
# ROLES — Définit les rôles métier (configurables depuis l'admin)
# =========================================================================


class Role(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Nom"))
    slug = models.CharField(max_length=50, unique=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_system = models.BooleanField(
        default=False, verbose_name=_("Système"),
        help_text=_("Les rôles système ne peuvent pas être supprimés"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    rank = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))

    class Meta:
        verbose_name = _("Rôle")
        verbose_name_plural = _("Rôles")
        ordering = ["rank", "name"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["rank"]),
        ]

    def __str__(self):
        return self.name


# =========================================================================
# PERMISSIONS — Permissions granulaires basées sur des codenames
# =========================================================================


class Permission(BaseModel):
    codename = models.CharField(max_length=100, unique=True, verbose_name=_("Code"))
    name = models.CharField(max_length=200, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    module = models.CharField(max_length=50, verbose_name=_("Module"))

    class Meta:
        verbose_name = _("Permission")
        verbose_name_plural = _("Permissions")
        ordering = ["module", "codename"]
        indexes = [
            models.Index(fields=["module"]),
        ]

    def __str__(self):
        return f"{self.module}.{self.codename}"


# =========================================================================
# ROLE PERMISSION — Association N-N Rôle → Permission
# =========================================================================


class RolePermission(BaseModel):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="role_permissions",
        verbose_name=_("Rôle"),
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions",
        verbose_name=_("Permission"),
    )

    class Meta:
        verbose_name = _("Permission de rôle")
        verbose_name_plural = _("Permissions de rôles")
        unique_together = [["role", "permission"]]

    def __str__(self):
        return f"{self.role.slug} → {self.permission.codename}"


# =========================================================================
# USER ROLE ASSIGNMENT — Rôles additionnels pour un utilisateur
# =========================================================================


class UserRoleAssignment(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="role_assignments",
        verbose_name=_("Utilisateur"),
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="user_assignments",
        verbose_name=_("Rôle"),
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="role_assignments_given", verbose_name=_("Assigné par"),
    )
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expire le"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))

    class Meta:
        verbose_name = _("Assignation de rôle")
        verbose_name_plural = _("Assignations de rôles")
        unique_together = [["user", "role"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.role.slug}"


# =========================================================================
# WORKFLOW PERMISSION — Associe des rôles aux transitions workflow
# =========================================================================


class WorkflowPermission(BaseModel):
    app_label = models.CharField(max_length=50, verbose_name=_("Application"))
    model_name = models.CharField(max_length=50, verbose_name=_("Modèle"))
    from_state = models.CharField(max_length=50, verbose_name=_("État source"))
    to_state = models.CharField(max_length=50, verbose_name=_("État cible"))
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="workflow_permissions",
        verbose_name=_("Rôle"),
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="workflow_permissions", verbose_name=_("Permission requise"),
    )

    class Meta:
        verbose_name = _("Permission de workflow")
        verbose_name_plural = _("Permissions de workflow")
        unique_together = [
            ["app_label", "model_name", "from_state", "to_state", "role"],
        ]
        ordering = ["app_label", "model_name", "from_state", "to_state"]
        indexes = [
            models.Index(fields=["app_label", "model_name", "from_state", "to_state"]),
        ]

    def __str__(self):
        return f"{self.app_label}.{self.model_name}: {self.from_state}→{self.to_state} [{self.role.slug}]"


# =========================================================================
# APPROVAL MATRIX — Règles d'approbation multi-niveaux (montant, rôle, etc.)
# =========================================================================


class ApprovalMatrix(BaseModel):
    module = models.CharField(max_length=50, verbose_name=_("Module"))
    min_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name=_("Montant min"),
    )
    max_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name=_("Montant max"),
    )
    approval_level = models.PositiveIntegerField(verbose_name=_("Niveau d'approbation"))
    required_roles = models.ManyToManyField(
        Role, related_name="approval_matrix_entries", verbose_name=_("Rôles requis"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = _("Matrice d'approbation")
        verbose_name_plural = _("Matrices d'approbation")
        ordering = ["module", "approval_level", "min_amount"]
        indexes = [
            models.Index(fields=["module", "is_active", "approval_level"]),
        ]

    def __str__(self):
        return f"{self.module} — Niveau {self.approval_level}"


# =========================================================================
# APPROVAL HISTORY — Suivi des approbations pour les demandes de couverture
# =========================================================================


class ApprovalHistory(BaseModel):
    ACTION_CHOICES = [
        ("auto_validated", _("Validation automatique")),
        ("approved", _("Approuvé")),
        ("rejected", _("Rejeté")),
        ("pending_manager", _("En attente manager")),
        ("escalated", _("Escaladé au directeur")),
        ("director_approved", _("Approuvé par le directeur")),
        ("director_rejected", _("Rejeté par le directeur")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        null=True, blank=True, verbose_name=_("Type de contenu"),
    )
    object_id = models.UUIDField(
        null=True, blank=True, verbose_name=_("ID de l'objet"),
    )
    content_object = GenericForeignKey("content_type", "object_id")
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name=_("Action"))
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approval_actions", verbose_name=_("Utilisateur"),
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))
    comment = models.TextField(blank=True, verbose_name=_("Commentaire"))
    from_state = models.CharField(max_length=50, blank=True, verbose_name=_("État précédent"))
    to_state = models.CharField(max_length=50, blank=True, verbose_name=_("Nouvel état"))

    class Meta:
        verbose_name = _("Historique d'approbation")
        verbose_name_plural = _("Historiques d'approbation")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} — {self.object_id}"
