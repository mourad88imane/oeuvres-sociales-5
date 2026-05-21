"""
============================================================
CORE MODELS — Fondation de tous les modèles du projet
============================================================
Principe : Tous les modèles héritent de BaseModel.
Cela garantit : UUID, timestamps, soft delete, historique.
"""

import uuid

from simple_history.models import HistoricalRecords

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet avec support soft delete."""

    def delete(self):
        """Soft delete en masse."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Suppression physique (admin uniquement)."""
        return super().delete()

    def alive(self):
        """Retourne uniquement les objets non supprimés."""
        return self.filter(is_deleted=False)

    def dead(self):
        """Retourne uniquement les objets supprimés (pour audit)."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager filtrant automatiquement les objets supprimés."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def with_deleted(self):
        """Inclure les objets supprimés (pour audit)."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def alive(self):
        return self.get_queryset()

    def dead(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class BaseModel(models.Model):
    """
    Modèle de base abstrait pour toute entité du système.

    Fournit :
    - UUID comme clé primaire (meilleur pour les APIs et la sécurité)
    - Timestamps automatiques (created_at, updated_at)
    - Traçabilité utilisateur (created_by, updated_by)
    - Soft delete (is_deleted, deleted_at)
    - Historique complet (django-simple-history) pour préparation AI
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identifiant unique universel",
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date de création")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date de dernière modification")
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        help_text="Utilisateur créateur",
    )
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        help_text="Dernier utilisateur modificateur",
    )
    is_deleted = models.BooleanField(default=False, help_text="Suppression logique (soft delete)")
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Date de suppression logique"
    )
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
        help_text="Utilisateur ayant supprimé",
    )

    # Historique complet pour audit et préparation AI
    history = HistoricalRecords(inherit=True)

    # Managers
    all_objects = models.Manager()  # Inclut tout (admin, audit)
    objects = SoftDeleteManager()  # Exclut les supprimés par défaut

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.__class__.__name__} ({self.id})"

    def save(self, *args, **kwargs):
        """Override save pour s'assurer que les FKs sont cohérentes."""
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """Suppression logique avec traçabilité."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])

    def restore(self):
        """Restauration d'un objet supprimé."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])
