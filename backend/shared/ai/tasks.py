import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .anomaly import AnomalyDetector
from .scoring import ScoringEngine
from .recommendations import RecommendationEngine
from .forecasting import ForecastingService
from .pipeline import AIPipeline
from .models import AIEvent, AIAnomaly, AIRecommendation, AIFeature

logger = logging.getLogger("shared.ai.tasks")

anomaly_detector = AnomalyDetector()
scoring_engine = ScoringEngine()
recommendation_engine = RecommendationEngine()
forecasting_service = ForecastingService()
ai_pipeline = AIPipeline()


@shared_task(name="run_ai_pipeline")
def run_ai_pipeline():
    """Run the full AI data pipeline: collect, transform, store features."""
    results = ai_pipeline.run()
    logger.info("AI pipeline completed: %s", results)
    return results


@shared_task(name="detect_anomalies_periodic")
def detect_anomalies_periodic():
    """Periodic anomaly detection across all targets."""
    results = anomaly_detector.detect_all(days=90, method="ensemble")
    count = len(results.get("kpi_anomalies", [])) + len(results.get("benefit_anomalies", []))
    logger.info("Periodic anomaly check: %d anomalies detected", count)
    return {"anomaly_count": count}


@shared_task(name="generate_recommendations_periodic")
def generate_recommendations_periodic():
    """Periodic recommendation generation."""
    results = recommendation_engine.generate_all()
    count = len(results)
    logger.info("Periodic recommendation generation: %d recommendations", count)
    return {"recommendation_count": count}


@shared_task(name="run_forecast_periodic")
def run_forecast_periodic():
    """Periodic forecasting run."""
    results = forecasting_service.forecast(target="benefits", months=6, method="ensemble")
    logger.info("Periodic forecast completed")
    return results


@shared_task(name="cleanup_old_ai_data")
def cleanup_old_ai_data(days=90):
    """Purge old AI data (events, features, expired recommendations)."""
    cutoff = timezone.now() - timedelta(days=days)
    deleted_events, _ = AIEvent.objects.filter(timestamp__lt=cutoff).delete()
    deleted_features, _ = AIFeature.objects.filter(computed_at__lt=cutoff).delete()
    deleted_anomalies, _ = AIAnomaly.objects.filter(
        created_at__lt=cutoff, status__in=["resolved", "false_positive"],
    ).delete()
    expired_recs = AIRecommendation.objects.filter(
        expires_at__lt=timezone.now(), feedback="pending",
    ).update(is_active=False)
    logger.info(
        "AI data cleanup: %d events, %d features, %d resolved anomalies, %d recs expired",
        deleted_events, deleted_features, deleted_anomalies, expired_recs,
    )
    return {
        "events": deleted_events,
        "features": deleted_features,
        "anomalies": deleted_anomalies,
        "recommendations_expired": expired_recs,
    }
