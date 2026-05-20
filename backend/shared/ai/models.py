"""
============================================================
AI MODELS — Stockage des prédictions, scores, anomalies,
recommandations, features, événements et registre de modèles
============================================================
"""
import uuid
from django.conf import settings
from django.db import models


class AIModelRegistry(models.Model):
    """
    Registre des modèles ML — versioning, cycle de vie, performance.
    Chaque modèle entraîné est enregistré ici.
    """
    class Status(models.TextChoices):
        DEV = "dev", "Développement"
        STAGING = "staging", "Test"
        PRODUCTION = "production", "Production"
        DEPRECATED = "deprecated", "Déprécié"
        ARCHIVED = "archived", "Archivé"

    class TaskType(models.TextChoices):
        ANOMALY = "anomaly", "Détection d'anomalies"
        SCORING = "scoring", "Scoring de demandes"
        FORECAST = "forecast", "Prévisions budgétaires"
        RECOMMENDATION = "recommendation", "Recommandations"
        BEHAVIOR = "behavior", "Analyse comportementale"
        ASSISTANT = "assistant", "Assistant IA"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    task_type = models.CharField(max_length=20, choices=TaskType.choices, db_index=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DEV)
    description = models.TextField(blank=True)
    algorithm = models.CharField(max_length=100, blank=True, help_text="Algorithme utilisé")
    features_used = models.JSONField(default=list, blank=True, help_text="Liste des features utilisées")
    training_date = models.DateTimeField(null=True, blank=True)
    training_duration_s = models.FloatField(null=True, blank=True)
    training_data_count = models.PositiveIntegerField(null=True, blank=True)
    metrics = models.JSONField(default=dict, blank=True, help_text="Métriques d'évaluation (accuracy, precision, recall, f1, mae, rmse)")
    hyperparams = models.JSONField(default=dict, blank=True)
    artifact_path = models.CharField(max_length=500, blank=True, help_text="Chemin vers l'artefact du modèle")
    metadata = models.JSONField(default=dict, blank=True)
    trained_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registre modèle IA"
        verbose_name_plural = "Registre modèles IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task_type", "status"]),
            models.Index(fields=["name", "version"]),
        ]
        unique_together = [("name", "version")]

    def __str__(self):
        return f"{self.name} v{self.version} ({self.get_task_type_display()})"


class AIPrediction(models.Model):
    """Stocke toutes les prédictions générées par les modèles IA."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        AIModelRegistry, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    prediction_type = models.CharField(max_length=30, db_index=True, help_text="Type de prédiction (trend, budget, scoring)")
    target_type = models.CharField(max_length=50, blank=True, help_text="Type d'objet prédit (Benefit, Budget, etc.)")
    target_id = models.CharField(max_length=255, blank=True)
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField(null=True, blank=True, help_text="Indice de confiance 0-1")
    features_used = models.JSONField(default=list, blank=True)
    explanation = models.JSONField(default=dict, blank=True, help_text="Explication de la prédiction (SHAP-like)")
    execution_time_ms = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text="Invalider manuellement les prédictions obsolètes")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Prédiction IA"
        verbose_name_plural = "Prédictions IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["prediction_type", "-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]


class AIAnomaly(models.Model):
    """Anomalies détectées par les modèles IA."""
    class Severity(models.TextChoices):
        LOW = "low", "Faible"
        MEDIUM = "medium", "Moyen"
        HIGH = "high", "Élevé"
        CRITICAL = "critical", "Critique"

    class Status(models.TextChoices):
        NEW = "new", "Nouveau"
        CONFIRMED = "confirmed", "Confirmé"
        FALSE_POSITIVE = "false_positive", "Faux positif"
        INVESTIGATING = "investigating", "En investigation"
        RESOLVED = "resolved", "Résolu"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        AIModelRegistry, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    detection_method = models.CharField(max_length=50, help_text="Méthode ayant détecté (zscore, iqr, moving_avg, seasonal, ensemble)")
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NEW)
    target_type = models.CharField(max_length=50, help_text="Type d'objet concerné")
    target_id = models.CharField(max_length=255)
    target_repr = models.CharField(max_length=500, blank=True)
    metric_name = models.CharField(max_length=100, blank=True, help_text="Nom de la métrique anormale")
    expected_value = models.FloatField(null=True, blank=True)
    actual_value = models.FloatField(null=True, blank=True)
    deviation = models.FloatField(null=True, blank=True, help_text="Écart absolu")
    deviation_pct = models.FloatField(null=True, blank=True, help_text="Écart en %")
    zscore = models.FloatField(null=True, blank=True)
    context = models.JSONField(default=dict, blank=True, help_text="Données contextuelles au moment de la détection")
    explanation = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Anomalie IA"
        verbose_name_plural = "Anomalies IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["severity", "status"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["detection_method"]),
        ]


class AIScore(models.Model):
    """Scores calculés avec explications (SHAP-like feature attribution)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        AIModelRegistry, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    score_type = models.CharField(max_length=30, db_index=True, help_text="Type de score (demand, risk, priority, fraud)")
    target_type = models.CharField(max_length=50)
    target_id = models.CharField(max_length=255)
    target_repr = models.CharField(max_length=500, blank=True)
    score = models.FloatField(help_text="Score 0-100")
    confidence = models.FloatField(null=True, blank=True, help_text="Confiance du modèle 0-1")
    features = models.JSONField(default=dict, blank=True, help_text="Features utilisées pour le score")
    feature_importance = models.JSONField(default=dict, blank=True, help_text="Importance de chaque feature (SHAP-like)")
    explanation = models.TextField(blank=True, help_text="Explication lisible du score")
    decision_boundary = models.FloatField(null=True, blank=True, help_text="Seuil de décision")
    recommendation = models.CharField(max_length=50, blank=True, help_text="Action recommandée")
    ai_metadata = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Date d'expiration du score")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Score IA"
        verbose_name_plural = "Scores IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["score_type", "-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["score"]),
        ]


class AIRecommendation(models.Model):
    """Recommandations générées avec suivi des retours utilisateur."""
    class Priority(models.TextChoices):
        LOW = "low", "Basse"
        MEDIUM = "medium", "Moyenne"
        HIGH = "high", "Haute"
        CRITICAL = "critical", "Critique"

    class Feedback(models.TextChoices):
        PENDING = "pending", "En attente"
        HELPFUL = "helpful", "Utile"
        NOT_HELPFUL = "not_helpful", "Pas utile"
        APPLIED = "applied", "Appliquée"
        DISMISSED = "dismissed", "Ignorée"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(
        AIModelRegistry, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    domain = models.CharField(max_length=30, db_index=True, help_text="Domaine (finance, conventions, benefits, hr)")
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    title = models.CharField(max_length=200)
    detail = models.TextField(blank=True)
    action_url = models.CharField(max_length=500, blank=True, help_text="Lien vers l'action")
    action_label = models.CharField(max_length=100, blank=True)
    source_data = models.JSONField(default=dict, blank=True, help_text="Données ayant généré la recommandation")
    confidence = models.FloatField(null=True, blank=True)
    feedback = models.CharField(max_length=15, choices=Feedback.choices, default=Feedback.PENDING)
    feedback_at = models.DateTimeField(null=True, blank=True)
    feedback_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True, help_text="La recommandation expire après cette date")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Recommandation IA"
        verbose_name_plural = "Recommandations IA"
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["domain", "priority"]),
            models.Index(fields=["feedback"]),
        ]


class AIFeature(models.Model):
    """Feature store — valeurs de features calculées pour le ML."""
    class FeatureType(models.TextChoices):
        NUMERIC = "numeric", "Numérique"
        CATEGORICAL = "categorical", "Catégorielle"
        BOOLEAN = "boolean", "Booléenne"
        TIMESTAMP = "timestamp", "Horodatage"
        TEXT = "text", "Texte"
        EMBEDDING = "embedding", "Embedding"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature_name = models.CharField(max_length=100, db_index=True)
    feature_type = models.CharField(max_length=15, choices=FeatureType.choices)
    entity_type = models.CharField(max_length=50, db_index=True, help_text="Type d'entité (Benefit, Employee, etc.)")
    entity_id = models.CharField(max_length=255, db_index=True)
    value_numeric = models.FloatField(null=True, blank=True)
    value_text = models.TextField(blank=True)
    value_bool = models.BooleanField(null=True)
    value_json = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=100, blank=True, help_text="Source de la feature (pipeline, model)")
    computed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ttl_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Durée de validité en secondes")

    class Meta:
        verbose_name = "Feature IA"
        verbose_name_plural = "Features IA"
        indexes = [
            models.Index(fields=["feature_name", "entity_type", "entity_id"]),
            models.Index(fields=["entity_type", "entity_id", "feature_name"]),
        ]


class AIEvent(models.Model):
    """Événements bruts pour l'analyse comportementale."""
    class EventCategory(models.TextChoices):
        NAVIGATION = "navigation", "Navigation"
        ACTION = "action", "Action utilisateur"
        WORKFLOW = "workflow", "Transition workflow"
        SEARCH = "search", "Recherche"
        EXPORT = "export", "Export"
        LOGIN = "login", "Connexion"
        API_CALL = "api_call", "Appel API"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    user_email = models.EmailField(blank=True)
    user_role = models.CharField(max_length=30, blank=True)
    session_id = models.CharField(max_length=100, blank=True, db_index=True)
    event_category = models.CharField(max_length=20, choices=EventCategory.choices)
    event_name = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.CharField(max_length=255, blank=True)
    properties = models.JSONField(default=dict, blank=True, help_text="Propriétés contextuelles de l'événement")
    duration_ms = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Événement IA"
        verbose_name_plural = "Événements IA"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["event_category", "event_name"]),
            models.Index(fields=["session_id"]),
            models.Index(fields=["-timestamp"]),
        ]


class AIFeedback(models.Model):
    """Retour utilisateur sur les prédictions/scores/recommandations."""
    class Rating(models.IntegerChoices):
        TERRIBLE = 1, "Pas du tout pertinent"
        POOR = 2, "Peu pertinent"
        NEUTRAL = 3, "Neutre"
        GOOD = 4, "Pertinent"
        EXCELLENT = 5, "Très pertinent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    feedback_type = models.CharField(max_length=20, help_text="Type (prediction, anomaly, score, recommendation)")
    target_type = models.CharField(max_length=50)
    target_id = models.CharField(max_length=255)
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    comment = models.TextField(blank=True)
    expected_value = models.FloatField(null=True, blank=True, help_text="Valeur attendue par l'utilisateur")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback IA"
        verbose_name_plural = "Feedbacks IA"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["feedback_type", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]
