import logging

from shared.workflow.engine import WorkflowDefinition, TransitionDef, WorkflowContext

logger = logging.getLogger("apps.medical_coverage.workflow")


def guard_check_approval_matrix(ctx: WorkflowContext) -> tuple[bool, str]:
    amount = ctx.metadata.get("approved_amount") if ctx.metadata else getattr(ctx.instance, "amount", None)
    if not amount:
        return True, ""
    from apps.administration.services import requires_director_approval
    if requires_director_approval("medical_coverage", amount):
        return False, f"Le montant ({amount}) dépasse le seuil d'escalade. Approbation du directeur requise."
    return True, ""


def guard_amount_positive(ctx: WorkflowContext) -> tuple[bool, str]:
    amount = getattr(ctx.instance, "amount", None)
    if amount is not None and amount <= 0:
        return False, "Le montant doit être supérieur à zéro."
    return True, ""


def hook_send_notification(ctx: WorkflowContext):
    pass


def hook_auto_escalate_if_needed(ctx: WorkflowContext):
    amount = getattr(ctx.instance, "amount", None) or ctx.metadata.get("approved_amount", 0)
    if not amount:
        return
    from apps.administration.services import requires_director_approval
    if requires_director_approval("medical_coverage", amount):
        ctx.instance.workflow_state = "pending_director_approval"
        ctx.instance.save(update_fields=["workflow_state", "updated_at"])
        logger.info(
            "Voucher auto-escalated to director approval",
            extra={"voucher_id": str(ctx.instance.pk), "amount": str(amount)},
        )


class MedicalCoverageWorkflow(WorkflowDefinition):
    db_enabled = True
    STATES = {
        "draft": {"label": "Brouillon", "is_initial": True, "is_final": False},
        "submitted": {"label": "Soumise", "is_initial": False, "is_final": False},
        "pending_approval": {"label": "En attente d'approbation", "is_initial": False, "is_final": False},
        "pending_director_approval": {
            "label": "En attente du directeur",
            "is_initial": False, "is_final": False,
        },
        "validated": {"label": "Validée", "is_initial": False, "is_final": False},
        "rejected": {"label": "Rejetée", "is_initial": False, "is_final": True},
        "printed": {"label": "Imprimée", "is_initial": False, "is_final": False},
        "closed": {"label": "Clôturée", "is_initial": False, "is_final": True},
    }

    TRANSITIONS = [
        TransitionDef("draft", "submitted", "Soumettre",
                       allowed_roles=["admin", "social_agent"],
                       guards=[guard_amount_positive],
                       after_hooks=[hook_send_notification, hook_auto_escalate_if_needed],
                       requires_reason=False),
        TransitionDef("submitted", "pending_approval", "Soumettre à validation",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=False),
        TransitionDef("submitted", "pending_director_approval", "Escalader au directeur",
                       allowed_roles=["admin", "social_agent", "department_manager"],
                       requires_reason=True, severity="HIGH"),
        TransitionDef("pending_approval", "validated", "Valider",
                       allowed_roles=["admin", "department_manager"],
                       guards=[guard_check_approval_matrix],
                       requires_reason=False, severity="MEDIUM"),
        TransitionDef("pending_approval", "rejected", "Rejeter",
                       allowed_roles=["admin", "department_manager"],
                       requires_reason=True, severity="HIGH"),
        TransitionDef("pending_approval", "pending_director_approval", "Escalader au directeur",
                       allowed_roles=["admin", "department_manager"],
                       requires_reason=True, severity="HIGH"),
        TransitionDef("pending_director_approval", "validated", "Approuver (Directeur)",
                       allowed_roles=["admin", "director"],
                       requires_reason=False, severity="HIGH"),
        TransitionDef("pending_director_approval", "rejected", "Rejeter (Directeur)",
                       allowed_roles=["admin", "director"],
                       requires_reason=True, severity="CRITICAL"),
        TransitionDef("validated", "printed", "Imprimer",
                       allowed_roles=["admin", "gestionnaire", "comptable"],
                       requires_reason=False, severity="LOW"),
        TransitionDef("printed", "closed", "Clôturer",
                       allowed_roles=["admin", "gestionnaire"],
                       requires_reason=False, severity="LOW"),
        TransitionDef("draft", "cancelled", "Annuler",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=True, severity="LOW"),
        TransitionDef("submitted", "cancelled", "Annuler",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=True, severity="MEDIUM"),
        TransitionDef("pending_approval", "cancelled", "Annuler",
                       allowed_roles=["admin"],
                       requires_reason=True, severity="MEDIUM"),
        TransitionDef("pending_director_approval", "cancelled", "Annuler",
                       allowed_roles=["admin"],
                       requires_reason=True, severity="MEDIUM"),
    ]

    def get_default_state(self):
        return "draft"


class MedicalCoverageRequestWorkflow(WorkflowDefinition):
    db_enabled = True
    STATES = {
        "draft": {"label": "Brouillon", "is_initial": True, "is_final": False},
        "submitted": {"label": "Soumise", "is_initial": False, "is_final": False},
        "pending_approval": {"label": "En attente d'approbation", "is_initial": False, "is_final": False},
        "pending_manager_approval": {
            "label": "En attente du chef de service",
            "is_initial": False, "is_final": False,
        },
        "pending_director_approval": {
            "label": "En attente du directeur",
            "is_initial": False, "is_final": False,
        },
        "validated": {"label": "Validée", "is_initial": False, "is_final": False},
        "rejected": {"label": "Rejetée", "is_initial": False, "is_final": True},
        "printed": {"label": "Imprimée", "is_initial": False, "is_final": False},
        "closed": {"label": "Clôturée", "is_initial": False, "is_final": True},
    }

    TRANSITIONS = [
        # Social Agent → submit
        TransitionDef("draft", "submitted", "Soumettre",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=False),
        # Automatic validation (system) or pending manager approval (system)
        TransitionDef("submitted", "validated", "Valider automatiquement",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=False, severity="LOW"),
        TransitionDef("submitted", "pending_manager_approval", "Soumettre au chef de service",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=False),
        # Department Manager actions
        TransitionDef("pending_manager_approval", "validated", "Approuver",
                       allowed_roles=["admin", "department_manager"],
                       requires_reason=False, severity="MEDIUM"),
        TransitionDef("pending_manager_approval", "rejected", "Rejeter",
                       allowed_roles=["admin", "department_manager"],
                       requires_reason=True, severity="HIGH"),
        TransitionDef("pending_manager_approval", "pending_director_approval",
                       "Escalader au directeur",
                       allowed_roles=["admin", "department_manager"],
                       requires_reason=True, severity="HIGH"),
        # Director actions
        TransitionDef("pending_director_approval", "validated", "Approuver",
                       allowed_roles=["admin", "director"],
                       requires_reason=False, severity="HIGH"),
        TransitionDef("pending_director_approval", "rejected", "Rejeter",
                       allowed_roles=["admin", "director"],
                       requires_reason=True, severity="CRITICAL"),
        # Print & close (same as before)
        TransitionDef("validated", "printed", "Imprimer",
                       allowed_roles=["admin", "gestionnaire", "comptable"],
                       requires_reason=False, severity="LOW"),
        TransitionDef("printed", "closed", "Clôturer",
                       allowed_roles=["admin", "gestionnaire"],
                       requires_reason=False, severity="LOW"),
        # Cancel
        TransitionDef("draft", "cancelled", "Annuler",
                       allowed_roles=["admin", "social_agent"],
                       requires_reason=True, severity="LOW"),
        TransitionDef("pending_manager_approval", "cancelled", "Annuler",
                       allowed_roles=["admin"],
                       requires_reason=True, severity="MEDIUM"),
        TransitionDef("pending_director_approval", "cancelled", "Annuler",
                       allowed_roles=["admin"],
                       requires_reason=True, severity="MEDIUM"),
    ]

    def get_default_state(self):
        return "draft"
