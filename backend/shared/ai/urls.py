from django.urls import path

from . import views

app_name = "ai"

urlpatterns = [
    # CRUD endpoints for AI models
    path(
        "models/",
        views.AIModelRegistryViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="model-list",
    ),
    path(
        "models/<uuid:pk>/",
        views.AIModelRegistryViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="model-detail",
    ),
    # Read-only endpoints for predictions, anomalies, scores, recommendations, features, events
    path(
        "predictions/",
        views.AIPredictionViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="prediction-list",
    ),
    path(
        "predictions/<uuid:pk>/",
        views.AIPredictionViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="prediction-detail",
    ),
    path(
        "anomalies/",
        views.AIAnomalyViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="anomaly-list",
    ),
    path(
        "anomalies/unresolved/",
        views.AIAnomalyViewSet.as_view(
            {
                "get": "unresolved",
            }
        ),
        name="anomaly-unresolved",
    ),
    path(
        "anomalies/<uuid:pk>/",
        views.AIAnomalyViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="anomaly-detail",
    ),
    path(
        "anomalies/<uuid:pk>/resolve/",
        views.AIAnomalyViewSet.as_view(
            {
                "post": "resolve",
            }
        ),
        name="anomaly-resolve",
    ),
    path(
        "scores/",
        views.AIScoreViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="score-list",
    ),
    path(
        "scores/<uuid:pk>/",
        views.AIScoreViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="score-detail",
    ),
    path(
        "recommendations/",
        views.AIRecommendationViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="recommendation-list",
    ),
    path(
        "recommendations/active/",
        views.AIRecommendationViewSet.as_view(
            {
                "get": "active",
            }
        ),
        name="recommendation-active",
    ),
    path(
        "recommendations/<uuid:pk>/",
        views.AIRecommendationViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="recommendation-detail",
    ),
    path(
        "recommendations/<uuid:pk>/feedback/",
        views.AIRecommendationViewSet.as_view(
            {
                "post": "feedback",
            }
        ),
        name="recommendation-feedback",
    ),
    path(
        "features/",
        views.AIFeatureViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="feature-list",
    ),
    path(
        "features/<uuid:pk>/",
        views.AIFeatureViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="feature-detail",
    ),
    path(
        "events/",
        views.AIEventViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="event-list",
    ),
    path(
        "events/<uuid:pk>/",
        views.AIEventViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="event-detail",
    ),
    path(
        "feedback/",
        views.AIFeedbackViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="feedback-list",
    ),
    path(
        "feedback/<uuid:pk>/",
        views.AIFeedbackViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="feedback-detail",
    ),
    # Service endpoints (actions, not CRUD)
    path(
        "services/forecast/",
        views.AIServiceViewSet.as_view(
            {
                "post": "forecast",
            }
        ),
        name="service-forecast",
    ),
    path(
        "services/what-if/",
        views.AIServiceViewSet.as_view(
            {
                "post": "what_if",
            }
        ),
        name="service-what-if",
    ),
    path(
        "services/detect-anomalies/",
        views.AIServiceViewSet.as_view(
            {
                "post": "detect_anomalies",
            }
        ),
        name="service-detect-anomalies",
    ),
    path(
        "services/score-benefit/",
        views.AIServiceViewSet.as_view(
            {
                "post": "score_benefit",
            }
        ),
        name="service-score-benefit",
    ),
    path(
        "services/generate-recommendations/",
        views.AIServiceViewSet.as_view(
            {
                "post": "generate_recommendations",
            }
        ),
        name="service-generate-recommendations",
    ),
    path(
        "services/ask-assistant/",
        views.AIServiceViewSet.as_view(
            {
                "post": "ask_assistant",
            }
        ),
        name="service-ask-assistant",
    ),
    path(
        "services/run-pipeline/",
        views.AIServiceViewSet.as_view(
            {
                "post": "run_pipeline",
            }
        ),
        name="service-run-pipeline",
    ),
    path(
        "services/behavior-analysis/",
        views.AIServiceViewSet.as_view(
            {
                "get": "behavior_analysis",
            }
        ),
        name="service-behavior-analysis",
    ),
    path(
        "services/segmentation/",
        views.AIServiceViewSet.as_view(
            {
                "get": "segmentation",
            }
        ),
        name="service-segmentation",
    ),
]
