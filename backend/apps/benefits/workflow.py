"""
============================================================
BENEFITS WORKFLOW — Définition du workflow des prestations
============================================================

États :
  draft       → Brouillon (saisie en cours)
  submitted   → Soumise (en attente de traitement)
  under_review→ En instruction (gestionnaire l'a prise en charge)
  validated   → Validée (approuvée, en attente de paiement)
  paid        → Payée (paiement effectué et confirmé)
  rejected    → Rejetée (refusée à n'importe quelle étape)
  cancelled   → Annulée (par le demandeur avant traitement)
  on_hold     → En attente (bloquée, complément requis)

Transitions autorisées :
  draft       → submitted   : agent/gestionnaire
  submitted   → under_review: gestionnaire
  submitted   → rejected    : gestionnaire (avec motif obligatoire)
  submitted   → on_hold     : gestionnaire (document manquant)
  under_review→ validated   : gestionnaire
  under_review→ rejected    : gestionnaire (avec motif)
  under_review→ on_hold     : gestionnaire
  on_hold     → submitted   : agent (après correction)
  on_hold     → cancelled   : agent
  validated   → paid        : comptable
  validated   → rejected    : comptable (avec motif)
  draft       → cancelled   : agent (son propre brouillon)
  submitted   → cancelled   : agent (avant prise en charge)

PRÉPARATION AI :
  - Chaque guard est testable unitairement → injectable par le moteur AI
  - duration_seconds → dataset pour prédiction des délais
  - Les métadonnées des transitions → features pour scoring
"""

import logging
from typing import TYPE_CHECKING

from shared.workflow.engine import TransitionDef, WorkflowContext, WorkflowDefinition

if TYPE_CHECKING:
    pass

logger = logging.getLogger("apps.benefits.workflow")


# ═══════════════════════════════════════════════════════════
# GUARDS — Règles métier de validation
# ═══════════════════════════════════════════════════════════


def guard_has_employee(ctx: WorkflowContext) -> tuple[bool, str]:
    """La prestation doit être associée à un employé actif."""
    emp = getattr(ctx.instance, "employee", None)
    if not emp:
        return False, "Aucun employé associé à cette demande."
    if emp.status != "active":
        return False, f"L'employé {emp.get_full_name()} n'est pas actif (statut : {emp.status})."
    return True, ""


def guard_has_benefit_type(ctx: WorkflowContext) -> tuple[bool, str]:
    """Un type de prestation doit être sélectionné."""
    if not getattr(ctx.instance, "benefit_type", None):
        return False, "Aucun type de prestation sélectionné."
    return True, ""


def guard_amount_positive(ctx: WorkflowContext) -> tuple[bool, str]:
    """Le montant demandé doit être positif."""
    amount = getattr(ctx.instance, "requested_amount", None)
    if amount is None or amount <= 0:
        return False, "Le montant demandé doit être supérieur à zéro."
    return True, ""


def guard_amount_within_limit(ctx: WorkflowContext) -> tuple[bool, str]:
    """Le montant ne doit pas dépasser le plafond du type de prestation."""
    instance = ctx.instance
    btype = getattr(instance, "benefit_type", None)
    amount = getattr(instance, "requested_amount", 0)
    if btype and btype.max_amount and amount > btype.max_amount:
        return (
            False,
            f"Montant ({amount:,.0f} DZD) dépasse le plafond "
            f"({btype.max_amount:,.0f} DZD) pour ce type de prestation.",
        )
    return True, ""


def guard_employee_eligible(ctx: WorkflowContext) -> tuple[bool, str]:
    """Vérifier l'éligibilité de l'employé pour ce type de prestation."""
    instance = ctx.instance
    emp = getattr(instance, "employee", None)
    btype = getattr(instance, "benefit_type", None)
    if not emp or not btype:
        return True, ""

    # Vérification ancienneté minimale
    if btype.min_seniority_years and emp.seniority_years is not None:
        if emp.seniority_years < btype.min_seniority_years:
            return (
                False,
                f"Ancienneté insuffisante. Requis : {btype.min_seniority_years} an(s). "
                f"Actuelle : {emp.seniority_years:.1f} an(s).",
            )
    return True, ""


def guard_no_duplicate_active(ctx: WorkflowContext) -> tuple[bool, str]:
    """
    Éviter les doublons : un employé ne peut pas avoir deux demandes
    actives du même type en même temps.
    """
    from apps.benefits.models import Benefit

    instance = ctx.instance
    emp = getattr(instance, "employee", None)
    btype = getattr(instance, "benefit_type", None)
    if not emp or not btype:
        return True, ""

    active_states = ["submitted", "under_review", "validated", "on_hold"]
    duplicate = (
        Benefit.objects.filter(
            employee=emp,
            benefit_type=btype,
            workflow_state__in=active_states,
            is_deleted=False,
        )
        .exclude(pk=instance.pk)
        .exists()
    )

    if duplicate:
        return (
            False,
            "Une demande active du même type existe déjà pour cet employé.",
        )
    return True, ""


def guard_payment_reference_set(ctx: WorkflowContext) -> tuple[bool, str]:
    """Pour passer à 'payée', une référence de paiement doit être fournie."""
    payment_ref = ctx.metadata.get("payment_reference") or getattr(
        ctx.instance, "payment_reference", ""
    )
    if not payment_ref:
        return False, "Une référence de paiement est obligatoire."
    return True, ""


def guard_approved_amount_set(ctx: WorkflowContext) -> tuple[bool, str]:
    """Pour valider, le montant approuvé doit être défini."""
    if not ctx.metadata:
        return True, ""
    approved = ctx.metadata.get("approved_amount") or getattr(ctx.instance, "approved_amount", None)
    if not approved or approved <= 0:
        return False, "Le montant approuvé est obligatoire pour valider la demande."
    return True, ""


# ═══════════════════════════════════════════════════════════
# HOOKS — Side effects avant/après transitions
# ═══════════════════════════════════════════════════════════


def hook_set_submitted_at(ctx: WorkflowContext):
    """Enregistre la date de soumission."""
    from django.utils import timezone

    ctx.instance.submitted_at = timezone.now()
    ctx.instance.save(update_fields=["submitted_at"])


def hook_set_validated_at(ctx: WorkflowContext):
    """Enregistre la date de validation et le montant approuvé."""
    from django.utils import timezone

    ctx.instance.validated_at = timezone.now()
    ctx.instance.validated_by = ctx.actor
    approved = ctx.metadata.get("approved_amount")
    if approved:
        ctx.instance.approved_amount = approved
    ctx.instance.save(update_fields=["validated_at", "validated_by", "approved_amount"])


def hook_set_paid_at(ctx: WorkflowContext):
    """Enregistre la date de paiement et la référence."""
    from django.utils import timezone

    ctx.instance.paid_at = timezone.now()
    payment_ref = ctx.metadata.get("payment_reference")
    if payment_ref:
        ctx.instance.payment_reference = payment_ref
    paid_amount = ctx.metadata.get("paid_amount")
    if paid_amount:
        ctx.instance.paid_amount = paid_amount
    ctx.instance.save(update_fields=["paid_at", "payment_reference", "paid_amount"])


def hook_set_rejected_reason(ctx: WorkflowContext):
    """Enregistre le motif de rejet."""
    from django.utils import timezone

    ctx.instance.rejected_at = timezone.now()
    ctx.instance.rejection_reason = ctx.reason
    ctx.instance.save(update_fields=["rejected_at", "rejection_reason"])


def hook_send_notification(ctx: WorkflowContext):
    """Déclenche une notification asynchrone via Celery."""
    try:
        from apps.benefits.tasks import notify_benefit_transition

        notify_benefit_transition.delay(
            benefit_id=str(ctx.instance.pk),
            to_state=ctx.to_state,
            actor_name=ctx.actor.get_full_name() if ctx.actor else "Système",
            reason=ctx.reason,
        )
    except Exception as e:
        logger.warning(f"Notification hook failed: {e}")


def hook_update_analytics(ctx: WorkflowContext):
    """
    Met à jour les données analytics de la prestation.
    Préparation pour le scoring AI.
    """
    try:
        instance = ctx.instance
        analytics = instance.analytics_data or {}
        analytics[f"{ctx.to_state}_at"] = ctx.timestamp.isoformat()
        if ctx.transition_duration_seconds:
            analytics[f"{ctx.from_state}_duration_seconds"] = ctx.transition_duration_seconds
        instance.analytics_data = analytics
        instance.save(update_fields=["analytics_data"])
    except Exception as e:
        logger.warning(f"Analytics hook failed: {e}")


# ═══════════════════════════════════════════════════════════
# DÉFINITION DU WORKFLOW
# ═══════════════════════════════════════════════════════════


class BenefitWorkflowDefinition(WorkflowDefinition):
    """
    Workflow complet des prestations sociales.
    Instancié une seule fois comme attribut de classe sur le modèle Benefit.
    """

    db_enabled = True

    STATES = {
        "draft": {
            "label": "Brouillon",
            "color": "#6B7280",
            "bg": "bg-gray-100",
            "text": "text-gray-700",
            "is_initial": True,
            "is_final": False,
            "description": "Demande en cours de saisie, non soumise.",
        },
        "submitted": {
            "label": "Soumise",
            "color": "#3B82F6",
            "bg": "bg-blue-100",
            "text": "text-blue-700",
            "is_initial": False,
            "is_final": False,
            "description": "Demande soumise, en attente de traitement.",
        },
        "under_review": {
            "label": "En instruction",
            "color": "#8B5CF6",
            "bg": "bg-purple-100",
            "text": "text-purple-700",
            "is_initial": False,
            "is_final": False,
            "description": "Prise en charge par un gestionnaire.",
        },
        "on_hold": {
            "label": "En attente",
            "color": "#F59E0B",
            "bg": "bg-amber-100",
            "text": "text-amber-700",
            "is_initial": False,
            "is_final": False,
            "description": "Bloquée, complément d'information requis.",
        },
        "validated": {
            "label": "Validée",
            "color": "#10B981",
            "bg": "bg-emerald-100",
            "text": "text-emerald-700",
            "is_initial": False,
            "is_final": False,
            "description": "Approuvée, en attente de paiement.",
        },
        "paid": {
            "label": "Payée",
            "color": "#059669",
            "bg": "bg-green-100",
            "text": "text-green-700",
            "is_initial": False,
            "is_final": True,
            "description": "Paiement effectué et confirmé.",
        },
        "rejected": {
            "label": "Rejetée",
            "color": "#EF4444",
            "bg": "bg-red-100",
            "text": "text-red-700",
            "is_initial": False,
            "is_final": True,
            "description": "Demande refusée.",
        },
        "cancelled": {
            "label": "Annulée",
            "color": "#9CA3AF",
            "bg": "bg-gray-100",
            "text": "text-gray-500",
            "is_initial": False,
            "is_final": True,
            "description": "Annulée par le demandeur.",
        },
    }

    # ── Ordre visuel des états (pour la timeline) ──────────
    STATE_ORDER = ["draft", "submitted", "under_review", "validated", "paid"]

    TRANSITIONS = [
        # ── Soumission ─────────────────────────────────────
        TransitionDef(
            from_state="draft",
            to_state="submitted",
            name="Soumettre",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            guards=[
                guard_has_employee,
                guard_has_benefit_type,
                guard_amount_positive,
                guard_amount_within_limit,
                guard_employee_eligible,
                guard_no_duplicate_active,
            ],
            after_hooks=[hook_set_submitted_at, hook_send_notification, hook_update_analytics],
            severity="LOW",
            description="Soumet la demande pour traitement.",
        ),
        # ── Prise en charge ────────────────────────────────
        TransitionDef(
            from_state="submitted",
            to_state="under_review",
            name="Prendre en charge",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            after_hooks=[hook_send_notification, hook_update_analytics],
            severity="LOW",
            description="Le gestionnaire prend en charge la demande.",
        ),
        # ── Mise en attente ────────────────────────────────
        TransitionDef(
            from_state="submitted",
            to_state="on_hold",
            name="Mettre en attente",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            requires_reason=True,
            after_hooks=[hook_send_notification, hook_update_analytics],
            severity="MEDIUM",
            description="Bloque la demande (document manquant, complément requis).",
        ),
        TransitionDef(
            from_state="under_review",
            to_state="on_hold",
            name="Mettre en attente",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            requires_reason=True,
            after_hooks=[hook_send_notification, hook_update_analytics],
            severity="MEDIUM",
        ),
        # ── Reprise après mise en attente ──────────────────
        TransitionDef(
            from_state="on_hold",
            to_state="submitted",
            name="Re-soumettre",
            allowed_roles=["admin", "gestionnaire"],
            after_hooks=[hook_update_analytics],
            is_reversal=False,
            severity="LOW",
            description="Remet la demande en file après correction.",
        ),
        # ── Validation ────────────────────────────────────
        TransitionDef(
            from_state="under_review",
            to_state="validated",
            name="Valider",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            guards=[guard_approved_amount_set],
            before_hooks=[hook_set_validated_at],
            after_hooks=[hook_send_notification, hook_update_analytics],
            severity="HIGH",
            description="Approuve la demande avec le montant validé.",
        ),
        TransitionDef(
            from_state="submitted",
            to_state="validated",
            name="Valider directement",
            allowed_roles=["admin"],
            guards=[guard_approved_amount_set],
            before_hooks=[hook_set_validated_at],
            after_hooks=[hook_send_notification, hook_update_analytics],
            severity="HIGH",
        ),
        # ── Paiement ──────────────────────────────────────
        TransitionDef(
            from_state="validated",
            to_state="paid",
            name="Confirmer le paiement",
            allowed_roles=["admin", "comptable"],
            guards=[guard_payment_reference_set],
            before_hooks=[hook_set_paid_at],
            after_hooks=[hook_send_notification, hook_update_analytics],
            severity="CRITICAL",
            description="Confirme le paiement avec la référence bancaire.",
        ),
        # ── Rejet (depuis plusieurs états) ────────────────
        TransitionDef(
            from_state="submitted",
            to_state="rejected",
            name="Rejeter",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification, hook_update_analytics],
            is_reversal=True,
            severity="HIGH",
        ),
        TransitionDef(
            from_state="under_review",
            to_state="rejected",
            name="Rejeter",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification, hook_update_analytics],
            is_reversal=True,
            severity="HIGH",
        ),
        TransitionDef(
            from_state="validated",
            to_state="rejected",
            name="Rejeter après validation",
            allowed_roles=["admin", "comptable"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification, hook_update_analytics],
            is_reversal=True,
            severity="CRITICAL",
        ),
        # ── Annulation ────────────────────────────────────
        TransitionDef(
            from_state="draft",
            to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin", "gestionnaire"],
            after_hooks=[hook_update_analytics],
            is_reversal=True,
            severity="LOW",
        ),
        TransitionDef(
            from_state="submitted",
            to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin", "gestionnaire", "department_manager"],
            requires_reason=True,
            after_hooks=[hook_send_notification, hook_update_analytics],
            is_reversal=True,
            severity="MEDIUM",
        ),
        TransitionDef(
            from_state="on_hold",
            to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin", "gestionnaire"],
            after_hooks=[hook_send_notification, hook_update_analytics],
            is_reversal=True,
            severity="MEDIUM",
        ),
    ]


# Instance globale (singleton) utilisée par le modèle Benefit
benefit_workflow = BenefitWorkflowDefinition()
