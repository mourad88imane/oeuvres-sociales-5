from django.conf import settings
from django.db import models
from core.models import BaseModel


class Notification(BaseModel):
    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-app"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"

    class Priority(models.TextChoices):
        LOW = "low", "Basse"
        MEDIUM = "medium", "Moyenne"
        HIGH = "high", "Haute"
        CRITICAL = "critical", "Critique"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinataire",
    )
    title = models.CharField(max_length=200, verbose_name="Titre")
    body = models.TextField(blank=True, verbose_name="Message")
    channel = models.CharField(
        max_length=10, choices=Channel.choices,
        default=Channel.IN_APP, verbose_name="Canal",
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name="Priorité",
    )
    is_read = models.BooleanField(default=False, verbose_name="Lue")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lue le")
    action_url = models.URLField(blank=True, verbose_name="Lien action")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icône")

    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Type de contenu",
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID objet")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["priority", "is_read"]),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} — {self.recipient}"

    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at", "updated_at"])


class NotificationPreference(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name="Utilisateur",
    )
    email_alerts = models.BooleanField(default=True, verbose_name="Notifications email")
    sms_alerts = models.BooleanField(default=False, verbose_name="Notifications SMS")
    push_alerts = models.BooleanField(default=False, verbose_name="Notifications push")
    digest_frequency = models.CharField(
        max_length=10,
        choices=[("instant", "Immédiat"), ("daily", "Quotidien"), ("weekly", "Hebdomadaire")],
        default="instant",
        verbose_name="Fréquence du digest",
    )
    quiet_hours_start = models.TimeField(null=True, blank=True, verbose_name="Début heures calmes")
    quiet_hours_end = models.TimeField(null=True, blank=True, verbose_name="Fin heures calmes")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")

    class Meta:
        verbose_name = "Préférence notification"
        verbose_name_plural = "Préférences notifications"

    def __str__(self):
        return f"Préférences — {self.user}"
