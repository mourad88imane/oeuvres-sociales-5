"""
============================================================
BENEFICIARY SERVICE — Logique métier ayants droit
============================================================
"""
import logging
from django.db import transaction
from django.db.models import QuerySet

from shared.audit.services import AuditService
from .models import Beneficiary

logger = logging.getLogger("apps.beneficiaries")
audit  = AuditService()


class BeneficiaryService:

    def get_queryset(self) -> QuerySet:
        return Beneficiary.objects.select_related("employee", "employee__department")

    # ── CRUD ─────────────────────────────────────────────
    @transaction.atomic
    def create(self, employee, validated_data: dict, user=None, request=None) -> Beneficiary:
        """Crée un ayant droit et calcule son éligibilité initiale."""
        bene = Beneficiary(employee=employee, **validated_data)
        if user:
            bene.created_by = user
            bene.updated_by = user
        bene.save()
        # Calcul automatique de l'éligibilité
        bene.update_eligibility()

        audit.log_create(user=user, obj=bene, request=request)
        logger.info("Beneficiary created", extra={
            "beneficiary_id": str(bene.id),
            "employee": employee.matricule,
            "relationship": bene.relationship,
        })
        return bene

    @transaction.atomic
    def update(self, bene: Beneficiary, validated_data: dict,
               user=None, request=None) -> Beneficiary:
        from django.forms.models import model_to_dict
        before_data = model_to_dict(bene)

        for attr, value in validated_data.items():
            setattr(bene, attr, value)
        if user:
            bene.updated_by = user
        bene.save()
        # Recalcul éligibilité après chaque modification
        bene.update_eligibility()

        audit.log_update(user=user, obj=bene,
                         before_data=before_data, request=request)
        return bene

    @transaction.atomic
    def delete(self, bene: Beneficiary, user=None, request=None):
        audit.log_delete(user=user, obj=bene, request=request)
        bene.soft_delete(user=user)

    def refresh_all_eligibility(self, employee) -> int:
        """
        Recalcule l'éligibilité de tous les ayants droit d'un employé.
        Appelé lors de changements de statut de l'employé.
        Retourne le nombre d'ayants droit mis à jour.
        """
        updated = 0
        for bene in employee.beneficiaries.filter(is_deleted=False):
            old = bene.is_eligible
            bene.update_eligibility()
            if bene.is_eligible != old:
                updated += 1
        return updated
