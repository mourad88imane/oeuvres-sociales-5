from django.contrib import admin

from .models import (
    AIAnomaly,
    AIEvent,
    AIFeature,
    AIFeedback,
    AIModelRegistry,
    AIPrediction,
    AIRecommendation,
    AIScore,
)


@admin.register(AIModelRegistry)
class AIModelRegistryAdmin(admin.ModelAdmin):
    list_display = ["name", "version", "task_type", "status", "trained_by", "created_at"]
    list_filter = ["task_type", "status"]
    search_fields = ["name", "description"]


@admin.register(AIPrediction)
class AIPredictionAdmin(admin.ModelAdmin):
    list_display = [
        "prediction_type",
        "target_type",
        "target_id",
        "confidence",
        "is_active",
        "created_at",
    ]
    list_filter = ["prediction_type", "is_active"]
    search_fields = ["target_type", "target_id"]


@admin.register(AIAnomaly)
class AIAnomalyAdmin(admin.ModelAdmin):
    list_display = [
        "metric_name",
        "severity",
        "status",
        "detection_method",
        "target_repr",
        "created_at",
    ]
    list_filter = ["severity", "status", "detection_method"]
    search_fields = ["target_repr", "metric_name"]


@admin.register(AIScore)
class AIScoreAdmin(admin.ModelAdmin):
    list_display = [
        "score_type",
        "target_repr",
        "score",
        "confidence",
        "recommendation",
        "created_at",
    ]
    list_filter = ["score_type", "recommendation"]
    search_fields = ["target_repr"]


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ["title", "domain", "priority", "feedback", "is_active", "created_at"]
    list_filter = ["domain", "priority", "feedback"]
    search_fields = ["title", "detail"]


@admin.register(AIFeature)
class AIFeatureAdmin(admin.ModelAdmin):
    list_display = ["feature_name", "feature_type", "entity_type", "entity_id", "computed_at"]
    list_filter = ["feature_type", "entity_type"]
    search_fields = ["feature_name", "entity_type", "entity_id"]


@admin.register(AIEvent)
class AIEventAdmin(admin.ModelAdmin):
    list_display = ["event_name", "event_category", "user_email", "user_role", "timestamp"]
    list_filter = ["event_category", "event_name"]
    search_fields = ["user_email", "event_name"]


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ["feedback_type", "target_type", "rating", "user", "created_at"]
    list_filter = ["feedback_type", "rating"]
    search_fields = ["target_type", "comment"]
