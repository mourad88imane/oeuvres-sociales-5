"""
============================================================
WORKFLOW ENGINE — Moteur d'états générique et réutilisable
============================================================

ARCHITECTURE :
  WorkflowDefinition  → définit les états et transitions possibles
  WorkflowTransition  → une transition autorisée (de → vers + règles)
  WorkflowMixin       → mixin Django à ajouter sur n'importe quel modèle
  WorkflowService     → service qui exécute les transitions avec guards

DESIGN POUR EXTENSIBILITÉ :
  - N'importe quel modèle Django peut devenir un workflow
    en héritant de WorkflowMixin
  - Les guards sont de simples callables Python → injectables, testables
  - Les hooks before/after permettent d'ajouter des side effects
    sans modifier le moteur
  - Préparé pour AI : chaque transition est loggée avec contexte complet
    (durée, acteur, raison, données) → dataset pour prédiction de délais

UTILISATION :
    class BenefitWorkflow(WorkflowDefinition):
        STATES = {...}
        TRANSITIONS = [...]

    class Benefit(WorkflowMixin, BaseModel):
        workflow = BenefitWorkflow()
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("apps.workflow")


# ── Types ──────────────────────────────────────────────────
Guard = Callable[["WorkflowContext"], tuple[bool, str]]
Hook = Callable[["WorkflowContext"], None]


@dataclass
class WorkflowContext:
    """
    Contexte d'une transition — passé à tous les guards et hooks.
    Contient toutes les informations nécessaires pour décider / logger.
    Préparé pour AI : toutes les données pertinentes sont structurées.
    """

    instance: Any  # L'objet Django
    from_state: str  # État source
    to_state: str  # État cible
    actor: Any  # Utilisateur déclencheur
    reason: str = ""  # Motif (obligatoire pour certaines transitions)
    metadata: dict = field(default_factory=dict)  # Données contextuelles (montant, ref, etc.)
    timestamp: datetime = field(default_factory=datetime.now)
    request: Any = None  # Requête HTTP (pour audit trail)

    # Champs calculés par le moteur
    transition_duration_seconds: float | None = None  # Durée dans l'état précédent (pour analytics)
    actor_role: str = ""


@dataclass
class TransitionDef:
    """
    Définition d'une transition autorisée dans le workflow.

    Champs :
      from_state  : état source ("*" = depuis n'importe quel état)
      to_state    : état cible
      name        : nom lisible (affiché dans l'UI et les logs)
      allowed_roles : rôles autorisés à déclencher cette transition
      guards      : liste de fonctions de validation (ctx) → (bool, str)
      before_hooks: hooks exécutés AVANT la transition (validation métier)
      after_hooks : hooks exécutés APRÈS la transition (notifications, logs)
      requires_reason : la transition exige un motif explicite
      is_reversal : c'est un retour en arrière (pour analytics)
      severity    : niveau pour l'audit (LOW/MEDIUM/HIGH/CRITICAL)
    """

    from_state: str
    to_state: str
    name: str
    allowed_roles: list[str] = field(default_factory=list)
    guards: list[Guard] = field(default_factory=list)
    before_hooks: list[Hook] = field(default_factory=list)
    after_hooks: list[Hook] = field(default_factory=list)
    requires_reason: bool = False
    is_reversal: bool = False
    severity: str = "LOW"
    description: str = ""


class WorkflowDefinition:
    """
    Classe de base pour définir un workflow.
    Hériter et déclarer STATES et TRANSITIONS.

    Exemple :
        class MonWorkflow(WorkflowDefinition):
            STATES = {
                "draft":  {"label": "Brouillon", "is_initial": True},
                "done":   {"label": "Terminé",   "is_final":   True},
            }
            TRANSITIONS = [
                TransitionDef("draft", "done", "Terminer",
                              allowed_roles=["admin"]),
            ]
    """

    STATES: dict[str, dict] = {}
    TRANSITIONS: list[TransitionDef] = []

    def get_transition(self, from_state: str, to_state: str) -> TransitionDef | None:
        for t in self.TRANSITIONS:
            if t.from_state == from_state and t.to_state == to_state:
                return t
            if t.from_state == "*" and t.to_state == to_state:
                return t
        return None

    def get_available_transitions(self, from_state: str, role: str = "") -> list[TransitionDef]:
        """Retourne les transitions disponibles depuis un état pour un rôle."""
        result = []
        for t in self.TRANSITIONS:
            if t.from_state not in (from_state, "*"):
                continue
            if t.allowed_roles and role and role not in t.allowed_roles:
                continue
            result.append(t)
        return result

    def get_state_label(self, state: str) -> str:
        return self.STATES.get(state, {}).get("label", state)

    def is_final_state(self, state: str) -> bool:
        return self.STATES.get(state, {}).get("is_final", False)

    def is_initial_state(self, state: str) -> bool:
        return self.STATES.get(state, {}).get("is_initial", False)


class WorkflowError(Exception):
    """Erreur de transition workflow — retournée comme 400 par l'API."""

    def __init__(self, message: str, code: str = "WORKFLOW_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class WorkflowEngine:
    """
    Moteur d'exécution des transitions.

    Responsabilités :
      1. Valider que la transition existe
      2. Vérifier les rôles
      3. Exécuter les guards (validation métier)
      4. Exécuter les hooks before
      5. Persister le changement d'état
      6. Logguer la transition (pour AI analytics)
      7. Exécuter les hooks after (notifications, etc.)
    """

    def __init__(self, definition: WorkflowDefinition):
        self.definition = definition

    def can_transition(
        self,
        instance,
        to_state: str,
        actor=None,
        reason: str = "",
        metadata: dict = None,
    ) -> tuple[bool, str]:
        """
        Vérifie si une transition est possible SANS l'exécuter.
        Utilisé par l'API pour afficher les actions disponibles dans l'UI.
        """
        from_state = instance.workflow_state
        transition = self.definition.get_transition(from_state, to_state)

        if not transition:
            return False, f"Transition {from_state} → {to_state} non définie."

        role = getattr(actor, "role", "") if actor else ""
        if transition.allowed_roles and role not in transition.allowed_roles:
            return False, f"Rôle '{role}' non autorisé pour cette transition."

        if transition.requires_reason and not reason:
            return False, "Un motif est obligatoire pour cette transition."

        ctx = WorkflowContext(
            instance=instance,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
            actor_role=role,
        )

        for guard in transition.guards:
            ok, msg = guard(ctx)
            if not ok:
                return False, msg

        return True, ""

    def transition(
        self,
        instance,
        to_state: str,
        actor=None,
        reason: str = "",
        metadata: dict = None,
        request=None,
    ) -> TransitionResult:
        """
        Exécute une transition de workflow.
        Retourne un TransitionResult avec le résultat.

        Lève WorkflowError si la transition est invalide.
        """
        from_state = instance.workflow_state
        role = getattr(actor, "role", "") if actor else ""

        # ── 1. Validation ──────────────────────────────────
        transition = self.definition.get_transition(from_state, to_state)
        if not transition:
            raise WorkflowError(
                f"Transition '{from_state}' → '{to_state}' non autorisée.",
                "INVALID_TRANSITION",
            )

        if transition.allowed_roles and role not in transition.allowed_roles:
            raise WorkflowError(
                f"Votre rôle ('{role}') ne peut pas effectuer : {transition.name}.",
                "FORBIDDEN_TRANSITION",
            )

        if transition.requires_reason and not reason:
            raise WorkflowError(
                "Un motif est obligatoire pour cette action.",
                "REASON_REQUIRED",
            )

        # ── 2. Calcul durée dans l'état précédent (analytics) ──
        duration = self._compute_state_duration(instance, from_state)

        ctx = WorkflowContext(
            instance=instance,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
            actor_role=role,
            request=request,
            transition_duration_seconds=duration,
        )

        # ── 3. Guards ──────────────────────────────────────
        for guard in transition.guards:
            ok, msg = guard(ctx)
            if not ok:
                raise WorkflowError(msg, "GUARD_FAILED")

        # ── 4. Hooks before ────────────────────────────────
        for hook in transition.before_hooks:
            hook(ctx)

        # ── 5. Persistance ─────────────────────────────────
        from django.utils import timezone

        old_state = instance.workflow_state
        instance.workflow_state = to_state
        instance.workflow_updated_at = timezone.now()
        if actor:
            instance.updated_by = actor
        instance.save(
            update_fields=["workflow_state", "workflow_updated_at", "updated_by", "updated_at"]
        )

        # ── 6. Log métier ──────────────────────────────────
        log_entry = self._log_transition(instance, transition, ctx)

        # ── 7. Hooks after ─────────────────────────────────
        for hook in transition.after_hooks:
            try:
                hook(ctx)
            except Exception as e:
                logger.error(f"Hook after-transition failed: {e}", exc_info=True)
                # Ne pas faire planter la transaction pour un hook

        logger.info(
            "Workflow transition",
            extra={
                "model": instance.__class__.__name__,
                "object_id": str(instance.pk),
                "from_state": old_state,
                "to_state": to_state,
                "actor": str(actor) if actor else "system",
                "reason": reason,
                "duration_s": duration,
            },
        )

        return TransitionResult(
            success=True,
            from_state=old_state,
            to_state=to_state,
            transition=transition,
            log_entry=log_entry,
        )

    def _compute_state_duration(self, instance, state: str) -> float | None:
        """Calcule le temps passé dans l'état courant (en secondes)."""
        try:
            from django.utils import timezone

            if hasattr(instance, "workflow_updated_at") and instance.workflow_updated_at:
                delta = timezone.now() - instance.workflow_updated_at
                return delta.total_seconds()
        except Exception:
            pass
        return None

    def _log_transition(self, instance, transition: TransitionDef, ctx: WorkflowContext):
        """Persiste la transition dans WorkflowLog pour audit et analytics AI."""
        try:
            from .models import WorkflowLog

            return WorkflowLog.objects.create(
                content_type_name=f"{instance._meta.app_label}.{instance._meta.model_name}",
                object_id=str(instance.pk),
                from_state=ctx.from_state,
                to_state=ctx.to_state,
                transition_name=transition.name,
                actor=ctx.actor,
                actor_role=ctx.actor_role,
                reason=ctx.reason,
                metadata=ctx.metadata,
                duration_seconds=ctx.transition_duration_seconds,
                is_reversal=transition.is_reversal,
                severity=transition.severity,
            )
        except Exception as e:
            logger.error(f"WorkflowLog creation failed: {e}", exc_info=True)
            return None


@dataclass
class TransitionResult:
    """Résultat d'une transition — retourné par WorkflowEngine.transition()."""

    success: bool
    from_state: str
    to_state: str
    transition: TransitionDef | None = None
    log_entry: Any = None
    error: str = ""
