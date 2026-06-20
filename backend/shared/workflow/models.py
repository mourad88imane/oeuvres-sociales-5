"""Workflow models — WorkflowLog + WorkflowMixin + Dynamic workflow models."""

import uuid

from django.conf import settings
from django.db import models


# ═══════════════════════════════════════════════════════════
# DYNAMIC WORKFLOW MODELS — Configurable from admin
# ═══════════════════════════════════════════════════════════


class WorkflowState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_label = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    state_id = models.CharField(max_length=50)
    label_fr = models.CharField(max_length=100)
    label_ar = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=7, default="#6B7280")
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "État de workflow"
        verbose_name_plural = "États de workflow"
        ordering = ["app_label", "model_name", "display_order"]
        unique_together = [("app_label", "model_name", "state_id")]

    def __str__(self):
        return f"[{self.app_label}.{self.model_name}] {self.state_id} — {self.label_fr}"


class WorkflowTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_label = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    from_state = models.ForeignKey(
        WorkflowState, on_delete=models.CASCADE,
        related_name="outgoing_transitions",
    )
    to_state = models.ForeignKey(
        WorkflowState, on_delete=models.CASCADE,
        related_name="incoming_transitions",
    )
    name = models.CharField(max_length=100)
    label_fr = models.CharField(max_length=100)
    label_ar = models.CharField(max_length=100, blank=True)
    requires_reason = models.BooleanField(default=False)
    is_reversal = models.BooleanField(default=False)
    severity = models.CharField(
        max_length=10,
        choices=[("LOW", "Faible"), ("MEDIUM", "Moyen"), ("HIGH", "Élevé"), ("CRITICAL", "Critique")],
        default="LOW",
    )
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transition de workflow"
        verbose_name_plural = "Transitions de workflow"
        ordering = ["app_label", "model_name", "display_order"]
        unique_together = [("app_label", "model_name", "from_state", "to_state")]

    def __str__(self):
        return f"[{self.app_label}.{self.model_name}] {self.from_state.state_id} → {self.to_state.state_id} ({self.name})"


class WorkflowTransitionRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transition = models.ForeignKey(
        WorkflowTransition, on_delete=models.CASCADE,
        related_name="allowed_roles",
    )
    role = models.ForeignKey(
        "administration.Role", on_delete=models.CASCADE,
        related_name="workflow_transition_roles",
    )
    permission = models.ForeignKey(
        "administration.Permission", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="workflow_transition_roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rôle autorisé pour transition"
        verbose_name_plural = "Rôles autorisés pour transitions"
        unique_together = [("transition", "role")]

    def __str__(self):
        return f"{self.transition} → {self.role.slug}"


# ═══════════════════════════════════════════════════════════
# WORKFLOW LOG (immutable audit trail)
# ═══════════════════════════════════════════════════════════


class WorkflowLog(models.Model):
    class Severity(models.TextChoices):
        LOW = "LOW", "Faible"
        MEDIUM = "MEDIUM", "Moyen"
        HIGH = "HIGH", "Élevé"
        CRITICAL = "CRITICAL", "Critique"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=255, db_index=True)
    from_state = models.CharField(max_length=50)
    to_state = models.CharField(max_length=50, db_index=True)
    transition_name = models.CharField(max_length=100)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_logs",
    )
    actor_email = models.EmailField(blank=True)
    actor_role = models.CharField(max_length=30, blank=True)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    is_reversal = models.BooleanField(default=False)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Log workflow"
        verbose_name_plural = "Logs workflow"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type_name", "object_id"]),
            models.Index(fields=["to_state", "-timestamp"]),
            models.Index(fields=["is_reversal", "-timestamp"]),
        ]

    def __str__(self):
        return (
            f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.object_id} {self.from_state}→{self.to_state}"
        )

    def save(self, *args, **kwargs):
        if self.pk and self.__class__.objects.filter(pk=self.pk).exists():
            raise PermissionError("Les logs workflow sont immuables.")
        if self.actor and not self.actor_email:
            self.actor_email = self.actor.email
        super().save(*args, **kwargs)

    @property
    def duration_label(self):
        if self.duration_seconds is None:
            return "—"
        s = int(self.duration_seconds)
        d, rem = divmod(s, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        parts = []
        if d:
            parts.append(f"{d}j")
        if h:
            parts.append(f"{h}h")
        if m:
            parts.append(f"{m}min")
        return " ".join(parts) or "< 1min"


class WorkflowMixin(models.Model):
    workflow_state = models.CharField(max_length=50, db_index=True)
    workflow_updated_at = models.DateTimeField(null=True, blank=True)
    last_transition_at = models.DateTimeField(null=True, blank=True)
    last_transition_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_last_transitions",
    )
    last_transition_reason = models.TextField(blank=True)

    class Meta:
        abstract = True

    @property
    def workflow_state_label(self):
        app = self._meta.app_label
        model = self._meta.model_name
        try:
            state = WorkflowState.objects.get(
                app_label=app, model_name=model,
                state_id=self.workflow_state, is_active=True,
            )
            return state.label_fr
        except WorkflowState.DoesNotExist:
            defn = getattr(self.__class__, "workflow_definition", None)
            return defn.get_state_label(self.workflow_state) if defn else self.workflow_state

    @property
    def is_final(self):
        app = self._meta.app_label
        model = self._meta.model_name
        try:
            state = WorkflowState.objects.get(
                app_label=app, model_name=model,
                state_id=self.workflow_state, is_active=True,
            )
            return state.is_final
        except WorkflowState.DoesNotExist:
            defn = getattr(self.__class__, "workflow_definition", None)
            return defn.is_final_state(self.workflow_state) if defn else False

    def get_available_transitions(self, role=""):
        app = self._meta.app_label
        model = self._meta.model_name
        transitions = WorkflowTransition.objects.filter(
            app_label=app, model_name=model,
            from_state__state_id=self.workflow_state,
            is_active=True,
        ).select_related("to_state", "from_state").order_by("display_order")
        if role:
            transitions = transitions.filter(
                allowed_roles__role__slug=role,
            ).distinct()
        return list(transitions)

    def get_workflow_logs(self):
        return WorkflowLog.objects.filter(
            content_type_name=f"{self._meta.app_label}.{self._meta.model_name}",
            object_id=str(self.pk),
        ).order_by("timestamp")
