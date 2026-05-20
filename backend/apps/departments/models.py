"""
============================================================
DEPARTMENTS MODELS
============================================================
Gestion des départements et structures organisationnelles.
Prêt pour analytics : hiérarchie, effectifs, budgets.
"""
from django.db import models
from core.models import BaseModel


class Department(BaseModel):
    """
    Département organisationnel.
    Supporte la hiérarchie (parent → enfants) pour les organigrammes futurs.
    """

    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code département",
        help_text="Code unique : RH, FIN, TECH, etc.",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Nom du département",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Département parent",
        help_text="Pour la hiérarchie organisationnelle",
    )
    manager = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name="Responsable",
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    # ── Préparation analytics ────────────────────────────
    budget_annual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Budget annuel (DZD)",
        help_text="Pour analytics budgétaires futurs",
    )
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Centre de coût",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Localisation",
    )

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"[{self.code}] {self.name}"

    @property
    def employee_count(self):
        """Nombre d'employés actifs dans ce département."""
        return self.employees.filter(
            status=Employee.Status.ACTIVE, is_deleted=False
        ).count()

    @property
    def full_path(self):
        """Chemin hiérarchique complet : DG / RH / Formation"""
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name


# Import circulaire résolu via string reference
from apps.employees.models import Employee  # noqa: E402
