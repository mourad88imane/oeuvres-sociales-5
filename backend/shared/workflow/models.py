"""Workflow models — WorkflowLog + WorkflowMixin."""

import uuid

from django.conf import settings
from django.db import models


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
        defn = getattr(self.__class__, "workflow_definition", None)
        return defn.get_state_label(self.workflow_state) if defn else self.workflow_state

    @property
    def is_final(self):
        defn = getattr(self.__class__, "workflow_definition", None)
        return defn.is_final_state(self.workflow_state) if defn else False

    def get_available_transitions(self, role=""):
        defn = getattr(self.__class__, "workflow_definition", None)
        if not defn:
            return []
        return defn.get_available_transitions(self.workflow_state, role)

    def get_workflow_logs(self):
        return WorkflowLog.objects.filter(
            content_type_name=f"{self._meta.app_label}.{self._meta.model_name}",
            object_id=str(self.pk),
        ).order_by("timestamp")
