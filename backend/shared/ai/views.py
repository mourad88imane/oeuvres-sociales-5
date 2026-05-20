import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import (
    AIModelRegistry, AIPrediction, AIAnomaly, AIScore,
    AIRecommendation, AIFeature, AIEvent, AIFeedback,
)
from .serializers import (
    AIModelRegistrySerializer, AIPredictionSerializer, AIAnomalySerializer,
    ResolveAnomalySerializer, AIScoreSerializer, AIRecommendationSerializer,
    RecommendationFeedbackSerializer, AIFeatureSerializer, AIEventSerializer,
    AIFeedbackSerializer, AssistantQuerySerializer, ForecastRequestSerializer,
    WhatIfSerializer,
)
from .anomaly import AnomalyDetector
from .scoring import ScoringEngine
from .recommendations import RecommendationEngine
from .forecasting import ForecastingService
from .behavior import BehaviorAnalyzer
from .assistant import AIAssistant
from .pipeline import AIPipeline

logger = logging.getLogger("shared.ai")

anomaly_detector = AnomalyDetector()
scoring_engine = ScoringEngine()
recommendation_engine = RecommendationEngine()
forecasting_service = ForecastingService()
behavior_analyzer = BehaviorAnalyzer()
ai_assistant = AIAssistant()
ai_pipeline = AIPipeline()


class AIModelRegistryViewSet(viewsets.ModelViewSet):
    queryset = AIModelRegistry.objects.all()
    serializer_class = AIModelRegistrySerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["task_type", "status", "name"]
    search_fields = ["name", "description"]


class AIPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIPrediction.objects.all()
    serializer_class = AIPredictionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["prediction_type", "target_type", "is_active"]
    ordering = ["-created_at"]


class AIAnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIAnomaly.objects.all()
    serializer_class = AIAnomalySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["severity", "status", "detection_method", "target_type"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        anomaly = self.get_object()
        serializer = ResolveAnomalySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        anomaly.status = serializer.validated_data["status"]
        anomaly.resolution_note = serializer.validated_data.get("resolution_note", "")
        anomaly.reviewed_by = request.user
        anomaly.reviewed_at = timezone.now()
        anomaly.save(update_fields=["status", "resolution_note", "reviewed_by", "reviewed_at"])
        return Response({"status": "success", "data": {"id": str(anomaly.pk), "status": anomaly.status}})

    @action(detail=False, methods=["get"])
    def unresolved(self, request):
        qs = self.get_queryset().filter(status__in=["new", "confirmed", "investigating"])
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({"status": "success", "data": serializer.data})


class AIScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIScore.objects.all()
    serializer_class = AIScoreSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["score_type", "target_type"]
    ordering = ["-created_at"]


class AIRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIRecommendation.objects.filter(is_active=True)
    serializer_class = AIRecommendationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["domain", "priority", "feedback"]
    ordering = ["-priority", "-created_at"]

    @action(detail=True, methods=["post"])
    def feedback(self, request, pk=None):
        recommendation = self.get_object()
        serializer = RecommendationFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recommendation.feedback = serializer.validated_data["feedback"]
        recommendation.feedback_at = timezone.now()
        recommendation.feedback_by = request.user
        if serializer.validated_data.get("comment"):
            recommendation.detail += f"\n[Feedback] {serializer.validated_data['comment']}"
        recommendation.save(update_fields=["feedback", "feedback_at", "feedback_by", "detail"])
        return Response({"status": "success", "data": {"id": str(recommendation.pk), "feedback": recommendation.feedback}})

    @action(detail=False, methods=["get"])
    def active(self, request):
        qs = self.get_queryset().filter(feedback="pending")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({"status": "success", "data": serializer.data})


class AIFeatureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIFeature.objects.all()
    serializer_class = AIFeatureSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["feature_name", "feature_type", "entity_type"]
    ordering = ["-computed_at"]


class AIEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIEvent.objects.all()
    serializer_class = AIEventSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["event_category", "event_name", "user_role"]
    ordering = ["-timestamp"]


class AIFeedbackViewSet(viewsets.ModelViewSet):
    queryset = AIFeedback.objects.all()
    serializer_class = AIFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["feedback_type", "target_type"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AIServiceViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def forecast(self, request):
        serializer = ForecastRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = forecasting_service.forecast(
            target=serializer.validated_data["target"],
            months=serializer.validated_data["months"],
            method=serializer.validated_data["method"],
        )
        return Response({"status": "success", "data": result})

    @action(detail=False, methods=["post"])
    def what_if(self, request):
        serializer = WhatIfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = forecasting_service.what_if_scenario(
            budget_change_pct=serializer.validated_data["budget_change_pct"],
            new_hires=serializer.validated_data["new_hires"],
        )
        return Response({"status": "success", "data": result})

    @action(detail=False, methods=["post"])
    def detect_anomalies(self, request):
        days = int(request.data.get("days", 90))
        method = request.data.get("method", "ensemble")
        results = anomaly_detector.detect_all(days=days, method=method)
        return Response({"status": "success", "data": results})

    @action(detail=False, methods=["post"])
    def score_benefit(self, request):
        benefit_id = request.data.get("benefit_id")
        if not benefit_id:
            return Response({"status": "error", "message": "benefit_id requis"}, status=400)
        result = scoring_engine.score_benefit(benefit_id, save=True)
        return Response({"status": "success", "data": result})

    @action(detail=False, methods=["post"])
    def generate_recommendations(self, request):
        user = request.user if request.user.is_authenticated else None
        results = recommendation_engine.generate_all(user=user)
        return Response({"status": "success", "data": results})

    @action(detail=False, methods=["post"])
    def ask_assistant(self, request):
        serializer = AssistantQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ai_assistant.process_query(
            serializer.validated_data["query"],
            user=request.user,
        )
        return Response({"status": "success", "data": result})

    @action(detail=False, methods=["post"])
    def run_pipeline(self, request):
        pipeline_type = request.data.get("type", "all")
        results = ai_pipeline.run(pipeline_type=pipeline_type)
        return Response({"status": "success", "data": results})

    @action(detail=False, methods=["get"])
    def behavior_analysis(self, request):
        days = int(request.query_params.get("days", 30))
        user_id = request.query_params.get("user_id")
        analysis = behavior_analyzer.analyze_user_activity(
            days=days, user_id=user_id,
        )
        risk_profiles = behavior_analyzer.get_user_risk_profiles(days=days)
        return Response({
            "status": "success",
            "data": {
                "activity_analysis": analysis,
                "risk_profiles": risk_profiles,
            },
        })

    @action(detail=False, methods=["get"])
    def segmentation(self, request):
        days = int(request.query_params.get("days", 30))
        segments = behavior_analyzer.segment_users(days=days)
        return Response({"status": "success", "data": segments})
