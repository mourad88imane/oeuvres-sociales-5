import logging

from shared.workflow.engine import TransitionDef, WorkflowContext, WorkflowDefinition

logger = logging.getLogger("apps.loans.workflow")


def guard_has_employee(ctx: WorkflowContext) -> tuple[bool, str]:
    emp = getattr(ctx.instance, "employee", None)
    if not emp:
        return False, "Aucun employé associé à cette demande."
    if emp.status != "active":
        return False, f"L'employé {emp.get_full_name()} n'est pas actif."
    return True, ""


def guard_amount_positive(ctx: WorkflowContext) -> tuple[bool, str]:
    amount = getattr(ctx.instance, "requested_amount", None)
    if amount is None or amount <= 0:
        return False, "Le montant demandé doit être supérieur à zéro."
    return True, ""


def guard_approved_amount_set(ctx: WorkflowContext) -> tuple[bool, str]:
    approved = (
        ctx.metadata.get("approved_amount") if ctx.metadata
        else getattr(ctx.instance, "approved_amount", None)
    )
    if not approved or approved <= 0:
        return False, "Le montant approuvé est obligatoire pour valider la demande."
    return True, ""


def guard_check_approval_matrix(ctx: WorkflowContext) -> tuple[bool, str]:
    """
    Vérifie si le montant demandé nécessite une escalation
    vers le directeur via la matrice d'approbation configurable.
    """
    amount = ctx.metadata.get("approved_amount") if ctx.metadata else getattr(ctx.instance, "requested_amount", None)
    if not amount:
        return True, ""
    from apps.administration.services import requires_director_approval
    if requires_director_approval("loans", amount):
        return False, f"Le montant ({amount}) dépasse le seuil d'escalade. Approbation du directeur requise."
    return True, ""


def guard_payment_reference_set(ctx: WorkflowContext) -> tuple[bool, str]:
    payment_ref = ctx.metadata.get("payment_reference") or getattr(ctx.instance, "payment_reference", "")
    if not payment_ref:
        return False, "Une référence de paiement est obligatoire."
    return True, ""


def hook_set_submitted_at(ctx: WorkflowContext):
    from django.utils import timezone
    ctx.instance.submitted_at = timezone.now()
    ctx.instance.save(update_fields=["submitted_at"])


def hook_set_validated_at(ctx: WorkflowContext):
    from django.utils import timezone
    ctx.instance.validated_at = timezone.now()
    ctx.instance.validated_by = ctx.actor
    approved = ctx.metadata.get("approved_amount")
    if approved:
        ctx.instance.approved_amount = approved
    monthly = ctx.metadata.get("monthly_instalment")
    if monthly:
        ctx.instance.monthly_instalment = monthly
    count = ctx.metadata.get("instalment_count")
    if count:
        ctx.instance.instalment_count = count
    ctx.instance.save(update_fields=["validated_at", "validated_by", "approved_amount",
                                     "monthly_instalment", "instalment_count"])


def hook_set_paid_at(ctx: WorkflowContext):
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
    from django.utils import timezone
    ctx.instance.rejected_at = timezone.now()
    ctx.instance.rejection_reason = ctx.reason
    ctx.instance.save(update_fields=["rejected_at", "rejection_reason"])


def hook_send_notification(ctx: WorkflowContext):
    try:
        from .tasks import notify_loan_transition
        notify_loan_transition.delay(
            loan_id=str(ctx.instance.pk),
            to_state=ctx.to_state,
            actor_name=ctx.actor.get_full_name() if ctx.actor else "Système",
            reason=ctx.reason,
        )
    except Exception as e:
        logger.warning(f"Notification hook failed: {e}")


def hook_auto_escalate_if_needed(ctx: WorkflowContext):
    """
    Vérifie la matrice d'approbation après soumission.
    Si le montant dépasse le seuil, redirige vers pending_director_approval.
    """
    amount = getattr(ctx.instance, "requested_amount", None) or ctx.metadata.get("approved_amount", 0)
    if not amount:
        return
    from apps.administration.services import requires_director_approval
    if requires_director_approval("loans", amount):
        ctx.instance.workflow_state = "pending_director_approval"
        ctx.instance.save(update_fields=["workflow_state", "updated_at"])
        logger.info(
            "Loan auto-escalated to director approval",
            extra={"loan_id": str(ctx.instance.pk), "amount": str(amount)},
        )


class LoanWorkflowDefinition(WorkflowDefinition):

    db_enabled = True

    STATES = {
        "draft": {
            "label": "Brouillon",
            "color": "#6B7280",
            "bg": "bg-gray-100",
            "text": "text-gray-700",
            "is_initial": True,
            "is_final": False,
            "description": "Demande en cours de saisie.",
        },
        "submitted": {
            "label": "Soumise",
            "color": "#3B82F6",
            "bg": "bg-blue-100",
            "text": "text-blue-700",
            "is_initial": False,
            "is_final": False,
            "description": "Soumise, en attente de traitement.",
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
            "description": "Complément d'information requis.",
        },
        "pending_director_approval": {
            "label": "En attente du directeur",
            "color": "#EC4899",
            "bg": "bg-pink-100",
            "text": "text-pink-700",
            "is_initial": False,
            "is_final": False,
            "description": "Nécessite approbation du directeur (montant élevé).",
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
            "description": "Paiement effectué.",
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

    STATE_ORDER = ["draft", "submitted", "under_review", "validated", "paid"]

    TRANSITIONS = [
        TransitionDef(
            from_state="draft", to_state="submitted",
            name="Soumettre",
            allowed_roles=["admin", "gestionnaire"],
            guards=[guard_has_employee, guard_amount_positive],
            after_hooks=[hook_set_submitted_at, hook_send_notification, hook_auto_escalate_if_needed],
            severity="LOW",
            description="Soumet la demande pour traitement.",
        ),
        TransitionDef(
            from_state="submitted", to_state="under_review",
            name="Prendre en charge",
            allowed_roles=["admin", "gestionnaire"],
            after_hooks=[hook_send_notification],
            severity="LOW",
            description="Le gestionnaire prend en charge la demande.",
        ),
        TransitionDef(
            from_state="submitted", to_state="on_hold",
            name="Mettre en attente",
            allowed_roles=["admin", "gestionnaire"],
            requires_reason=True,
            after_hooks=[hook_send_notification],
            severity="MEDIUM",
            description="Bloque la demande (complément requis).",
        ),
        TransitionDef(
            from_state="submitted", to_state="pending_director_approval",
            name="Escalader au directeur",
            allowed_roles=["admin", "gestionnaire"],
            requires_reason=True,
            after_hooks=[hook_send_notification],
            severity="HIGH",
            description="Transmettre au directeur pour approbation.",
        ),
        TransitionDef(
            from_state="under_review", to_state="on_hold",
            name="Mettre en attente",
            allowed_roles=["admin", "gestionnaire"],
            requires_reason=True,
            after_hooks=[hook_send_notification],
            severity="MEDIUM",
        ),
        TransitionDef(
            from_state="on_hold", to_state="submitted",
            name="Re-soumettre",
            allowed_roles=["admin", "gestionnaire"],
            severity="LOW",
            description="Remet en file après correction.",
        ),
        TransitionDef(
            from_state="under_review", to_state="validated",
            name="Valider",
            allowed_roles=["admin", "gestionnaire"],
            guards=[guard_approved_amount_set, guard_check_approval_matrix],
            before_hooks=[hook_set_validated_at],
            after_hooks=[hook_send_notification],
            severity="HIGH",
            description="Approuve la demande avec le montant validé.",
        ),
        TransitionDef(
            from_state="submitted", to_state="validated",
            name="Valider directement",
            allowed_roles=["admin"],
            guards=[guard_approved_amount_set],
            before_hooks=[hook_set_validated_at],
            after_hooks=[hook_send_notification],
            severity="HIGH",
        ),
        # Director approval transitions
        TransitionDef(
            from_state="pending_director_approval", to_state="validated",
            name="Approuver (Directeur)",
            allowed_roles=["admin", "director"],
            guards=[guard_approved_amount_set],
            before_hooks=[hook_set_validated_at],
            after_hooks=[hook_send_notification],
            severity="HIGH",
            description="Le directeur approuve la demande.",
        ),
        TransitionDef(
            from_state="pending_director_approval", to_state="rejected",
            name="Rejeter (Directeur)",
            allowed_roles=["admin", "director"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="CRITICAL",
            description="Le directeur refuse la demande.",
        ),
        TransitionDef(
            from_state="validated", to_state="paid",
            name="Confirmer le paiement",
            allowed_roles=["admin", "comptable"],
            guards=[guard_payment_reference_set],
            before_hooks=[hook_set_paid_at],
            after_hooks=[hook_send_notification],
            severity="CRITICAL",
            description="Confirme le paiement avec la référence bancaire.",
        ),
        TransitionDef(
            from_state="submitted", to_state="rejected",
            name="Rejeter",
            allowed_roles=["admin", "gestionnaire"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="HIGH",
        ),
        TransitionDef(
            from_state="under_review", to_state="rejected",
            name="Rejeter",
            allowed_roles=["admin", "gestionnaire"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="HIGH",
        ),
        TransitionDef(
            from_state="validated", to_state="rejected",
            name="Rejeter après validation",
            allowed_roles=["admin", "comptable"],
            requires_reason=True,
            before_hooks=[hook_set_rejected_reason],
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="CRITICAL",
        ),
        TransitionDef(
            from_state="draft", to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin", "gestionnaire"],
            severity="LOW",
        ),
        TransitionDef(
            from_state="submitted", to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin", "gestionnaire"],
            requires_reason=True,
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="MEDIUM",
        ),
        TransitionDef(
            from_state="on_hold", to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin", "gestionnaire"],
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="MEDIUM",
        ),
        TransitionDef(
            from_state="pending_director_approval", to_state="cancelled",
            name="Annuler",
            allowed_roles=["admin"],
            requires_reason=True,
            after_hooks=[hook_send_notification],
            is_reversal=True,
            severity="MEDIUM",
        ),
    ]


loan_workflow = LoanWorkflowDefinition()
