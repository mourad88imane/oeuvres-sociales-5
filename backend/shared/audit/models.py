"""
============================================================
AUDIT TRAIL — Historique complet des actions
============================================================
PRÉPARATION AI : Ce modèle est la source de vérité pour :
  - Détection d'anomalies (comportements inhabituels)
  - Analytics comportementaux
  - Recommandations basées sur l'historique
  - Conformité et traçabilité réglementaire

Chaque action CREATE/UPDATE/DELETE sur un objet métier
génère une entrée dans ce journal immuable.
"""
import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Journal d'audit immuable.
    Enregistre toutes les actions sur les données sensibles.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Création"
        UPDATE = "UPDATE", "Modification"
        DELETE = "DELETE", "Suppression"
        VIEW = "VIEW", "Consultation"
        LOGIN = "LOGIN", "Connexion"
        LOGOUT = "LOGOUT", "Déconnexion"
        LOGIN_FAILED = "LOGIN_FAILED", "Tentative échouée"
        EXPORT = "EXPORT", "Export"
        APPROVE = "APPROVE", "Validation"
        REJECT = "REJECT", "Rejet"
        SUBMIT = "SUBMIT", "Soumission"
        PAY = "PAY", "Paiement"
        WORKFLOW_TRANSITION = "WORKFLOW_TRANSITION", "Transition workflow"
        VALIDATE = "VALIDATE", "Validation"
        CERTIFY = "CERTIFY", "Certification"
        SIGN = "SIGN", "Signature"
        AUDIT_ACCESS = "AUDIT_ACCESS", "Consultation audit"
        ARCHIVE = "ARCHIVE", "Archivage"
        RESTORE = "RESTORE", "Restauration"
        IMPERSONATE = "IMPERSONATE", "Impersonnalisation"
        CONFIG_CHANGE = "CONFIG_CHANGE", "Modification configuration"
        BULK_OPERATION = "BULK_OPERATION", "Opération en masse"

    class Severity(models.TextChoices):
        LOW = "LOW", "Faible"
        MEDIUM = "MEDIUM", "Moyen"
        HIGH = "HIGH", "Élevé"
        CRITICAL = "CRITICAL", "Critique"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Qui ──────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="Utilisateur ayant effectué l'action"
    )
    user_email = models.EmailField(
        blank=True,
        help_text="Email dupliqué pour conservation après suppression user"
    )
    user_role = models.CharField(
        max_length=20,
        blank=True,
        help_text="Rôle au moment de l'action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Adresse IP de l'utilisateur"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User-Agent du navigateur"
    )

    # ── Quoi ─────────────────────────────────────────────
    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        help_text="Type d'action effectuée"
    )
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.LOW,
        help_text="Niveau de criticité"
    )

    # ── Sur quoi ─────────────────────────────────────────
    content_type_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nom du modèle concerné (ex: benefits.Benefit)"
    )
    object_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID de l'objet concerné"
    )
    object_repr = models.CharField(
        max_length=500,
        blank=True,
        help_text="Représentation textuelle de l'objet"
    )

    # ── Données pour AI ──────────────────────────────────
    before_data = models.JSONField(
        null=True,
        blank=True,
        help_text="État avant modification (pour diff et ML)"
    )
    after_data = models.JSONField(
        null=True,
        blank=True,
        help_text="État après modification (pour diff et ML)"
    )
    changed_fields = models.JSONField(
        null=True,
        blank=True,
        help_text="Liste des champs modifiés"
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données contextuelles supplémentaires"
    )

    # ── Contexte technique ───────────────────────────────
    request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID unique de la requête HTTP (pour corrélation logs)"
    )
    endpoint = models.CharField(
        max_length=500,
        blank=True,
        help_text="Endpoint API appelé"
    )
    http_method = models.CharField(max_length=10, blank=True)

    # ── Timestamp ────────────────────────────────────────
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Horodatage exact de l'action"
    )

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["action", "-timestamp"]),
            models.Index(fields=["content_type_name", "object_id"]),
            models.Index(fields=["severity", "-timestamp"]),
            models.Index(fields=["-timestamp"]),
        ]
        # Empêcher la modification des logs (immuabilité)

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user_email} — {self.action} — {self.content_type_name}"

    def save(self, *args, **kwargs):
        """Rendre le log immuable : pas de modification possible."""
        if self.pk:
            raise PermissionError("Les logs d'audit sont immuables.")
        # Dénormaliser les données utilisateur pour la conservation à long terme
        if self.user and not self.user_email:
            self.user_email = self.user.email
            self.user_role = self.user.role
        super().save(*args, **kwargs)
