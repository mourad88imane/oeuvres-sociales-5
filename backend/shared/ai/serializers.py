from rest_framework import serializers

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


class AIModelRegistrySerializer(serializers.ModelSerializer):
    task_type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    trained_by_email = serializers.EmailField(source="trained_by.email", read_only=True, default="")

    class Meta:
        model = AIModelRegistry
        fields = [
            "id",
            "name",
            "version",
            "task_type",
            "task_type_display",
            "status",
            "status_display",
            "description",
            "algorithm",
            "features_used",
            "training_date",
            "training_duration_s",
            "training_data_count",
            "metrics",
            "hyperparams",
            "artifact_path",
            "metadata",
            "trained_by",
            "trained_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AIPredictionSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = AIPrediction
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince

        return timesince(obj.created_at)


class AIAnomalySerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = AIAnomaly
        fields = "__all__"
        read_only_fields = ["id", "created_at", "reviewed_at"]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince

        return timesince(obj.created_at)


class ResolveAnomalySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["confirmed", "false_positive", "resolved"])
    resolution_note = serializers.CharField(required=False, allow_blank=True)


class AIScoreSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = AIScore
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince

        return timesince(obj.created_at)


class AIRecommendationSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    feedback_display = serializers.CharField(source="get_feedback_display", read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = AIRecommendation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "feedback_at"]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince

        return timesince(obj.created_at)


class RecommendationFeedbackSerializer(serializers.Serializer):
    feedback = serializers.ChoiceField(choices=["helpful", "not_helpful", "applied", "dismissed"])
    comment = serializers.CharField(required=False, allow_blank=True)


class AIFeatureSerializer(serializers.ModelSerializer):
    feature_type_display = serializers.CharField(source="get_feature_type_display", read_only=True)

    class Meta:
        model = AIFeature
        fields = "__all__"
        read_only_fields = ["id", "computed_at"]


class AIEventSerializer(serializers.ModelSerializer):
    event_category_display = serializers.CharField(
        source="get_event_category_display", read_only=True
    )
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = AIEvent
        fields = "__all__"
        read_only_fields = ["id", "timestamp"]

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince

        return timesince(obj.timestamp)


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class AssistantQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True, min_length=1, max_length=2000)


class ForecastRequestSerializer(serializers.Serializer):
    target = serializers.ChoiceField(choices=["benefits", "budget", "kpi"], default="benefits")
    months = serializers.IntegerField(default=6, min_value=1, max_value=24)
    method = serializers.ChoiceField(
        choices=["linear", "monte_carlo", "seasonal", "ensemble"],
        default="ensemble",
    )


class WhatIfSerializer(serializers.Serializer):
    budget_change_pct = serializers.FloatField(default=0.0, help_text="% de changement budgétaire")
    new_hires = serializers.IntegerField(default=0, min_value=0)
