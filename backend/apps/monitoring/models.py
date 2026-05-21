import uuid

from django.conf import settings
from django.db import models


class APIRequestLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=500)
    path = models.CharField(max_length=500)
    query_params = models.JSONField(default=dict, blank=True)
    status_code = models.PositiveSmallIntegerField()
    duration_ms = models.PositiveIntegerField(help_text="Temps de réponse en ms")
    response_size = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Requête API"
        verbose_name_plural = "Requêtes API"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["method", "endpoint"]),
            models.Index(fields=["status_code"]),
            models.Index(fields=["is_error", "-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} ({self.status_code})"


class SecurityEvent(models.Model):
    class EventType(models.TextChoices):
        LOGIN_FAILED = "LOGIN_FAILED", "Échec connexion"
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Connexion réussie"
        LOGOUT = "LOGOUT", "Déconnexion"
        PERMISSION_DENIED = "PERMISSION_DENIED", "Permission refusée"
        RATE_LIMITED = "RATE_LIMITED", "Limite de débit atteinte"
        BRUTE_FORCE = "BRUTE_FORCE", "Attaque brute force"
        SUSPICIOUS_IP = "SUSPICIOUS_IP", "IP suspecte"
        SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY", "Activité suspecte"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Mot de passe changé"
        ACCOUNT_LOCKED = "ACCOUNT_LOCKED", "Compte verrouillé"
        ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED", "Compte déverrouillé"
        SESSION_EXPIRED = "SESSION_EXPIRED", "Session expirée"
        API_ABUSE = "API_ABUSE", "Abus API"
        DATA_EXPORT = "DATA_EXPORT", "Export de données"
        SENSITIVE_ACCESS = "SENSITIVE_ACCESS", "Accès données sensibles"

    class Severity(models.TextChoices):
        INFO = "INFO", "Information"
        LOW = "LOW", "Faible"
        MEDIUM = "MEDIUM", "Moyen"
        HIGH = "HIGH", "Élevé"
        CRITICAL = "CRITICAL", "Critique"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user_email = models.EmailField(blank=True)
    user_role = models.CharField(max_length=20, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    endpoint = models.CharField(max_length=500, blank=True)
    details = models.JSONField(default=dict, blank=True)
    action_taken = models.CharField(max_length=200, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_events_resolved",
    )
    resolution_note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Événement sécurité"
        verbose_name_plural = "Événements sécurité"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["event_type", "-timestamp"]),
            models.Index(fields=["severity", "-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["ip_address", "-timestamp"]),
            models.Index(fields=["resolved", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} ({self.severity})"


class BusinessMetric(models.Model):
    class MetricType(models.TextChoices):
        API_CALLS = "API_CALLS", "Appels API"
        API_ERRORS = "API_ERRORS", "Erreurs API"
        API_DURATION = "API_DURATION", "Temps de réponse moyen"
        ACTIVE_USERS = "ACTIVE_USERS", "Utilisateurs actifs"
        NEW_USERS = "NEW_USERS", "Nouveaux utilisateurs"
        TOTAL_OBJECTS = "TOTAL_OBJECTS", "Nombre d'objets"
        WORKFLOW_COUNT = "WORKFLOW_COUNT", "Transitions workflow"
        EXPORT_COUNT = "EXPORT_COUNT", "Exports générés"
        STORAGE_USED = "STORAGE_USED", "Stockage utilisé"
        CACHE_HIT_RATE = "CACHE_HIT_RATE", "Taux de cache"
        CELERY_QUEUE = "CELERY_QUEUE", "File Celery"
        ERROR_COUNT = "ERROR_COUNT", "Nombre d'erreurs"

    class Granularity(models.TextChoices):
        MINUTE = "1m", "1 minute"
        HOUR = "1h", "1 heure"
        DAY = "24h", "24 heures"
        WEEK = "7d", "7 jours"
        MONTH = "30d", "30 jours"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=30, choices=MetricType.choices, db_index=True)
    granularity = models.CharField(
        max_length=5, choices=Granularity.choices, default=Granularity.HOUR
    )
    value = models.FloatField()
    label = models.CharField(
        max_length=100, blank=True, help_text="Libellé optionnel (ex: endpoint name)"
    )
    tags = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "Métrique métier"
        verbose_name_plural = "Métriques métier"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["metric_type", "granularity", "timestamp"]),
            models.Index(fields=["-timestamp"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["metric_type", "granularity", "label", "timestamp"],
                name="uq_metric_grain_label_ts",
            ),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.value} ({self.timestamp})"


class APIEndpointStatus(models.Model):
    endpoint = models.CharField(max_length=500, unique=True)
    method = models.CharField(max_length=10)
    total_calls = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    avg_duration_ms = models.FloatField(default=0)
    max_duration_ms = models.PositiveIntegerField(default=0)
    min_duration_ms = models.PositiveIntegerField(default=0)
    last_called = models.DateTimeField(null=True, blank=True)
    last_status = models.PositiveSmallIntegerField(null=True, blank=True)
    is_degraded = models.BooleanField(default=False)
    degraded_since = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Statut endpoint API"
        verbose_name_plural = "Statuts endpoints API"
        ordering = ["-total_calls"]
        indexes = [
            models.Index(fields=["endpoint"]),
            models.Index(fields=["is_degraded"]),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint}"
