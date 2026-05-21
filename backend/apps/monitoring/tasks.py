import logging
from datetime import timedelta

from celery import shared_task

from django.db.models import Avg
from django.utils import timezone

from .models import APIEndpointStatus, APIRequestLog, BusinessMetric, SecurityEvent

logger = logging.getLogger("apps.monitoring.tasks")


@shared_task(name="aggregate_api_metrics")
def aggregate_api_metrics():
    """Aggregate API metrics into BusinessMetric for time-series charts."""
    now = timezone.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    # Hourly aggregation
    for since, grain in [(hour_ago, "1h"), (day_ago, "24h")]:
        recent = APIRequestLog.objects.filter(timestamp__gte=since)
        total = recent.count()
        errors = recent.filter(is_error=True).count()
        avg_dur = recent.aggregate(avg=Avg("duration_ms"))["avg"] or 0

        BusinessMetric.objects.update_or_create(
            metric_type=BusinessMetric.MetricType.API_CALLS,
            granularity=grain,
            label="total",
            timestamp=since,
            defaults={"value": total},
        )
        BusinessMetric.objects.update_or_create(
            metric_type=BusinessMetric.MetricType.API_ERRORS,
            granularity=grain,
            label="total",
            timestamp=since,
            defaults={"value": errors},
        )
        BusinessMetric.objects.update_or_create(
            metric_type=BusinessMetric.MetricType.API_ERRORS,
            granularity=grain,
            label="error_rate",
            timestamp=since,
            defaults={"value": round(errors / max(total, 1) * 100, 2)},
        )
        BusinessMetric.objects.update_or_create(
            metric_type=BusinessMetric.MetricType.API_DURATION,
            granularity=grain,
            label="avg",
            timestamp=since,
            defaults={"value": round(avg_dur, 1)},
        )

    logger.info("API metrics aggregated for hour ending %s", now)
    return True


@shared_task(name="cleanup_old_monitoring_data")
def cleanup_old_monitoring_data(days=90):
    """Purge raw API logs older than `days`; keep aggregated metrics."""
    cutoff = timezone.now() - timedelta(days=days)
    deleted_logs, _ = APIRequestLog.objects.filter(timestamp__lt=cutoff).delete()
    deleted_security, _ = SecurityEvent.objects.filter(
        timestamp__lt=cutoff,
        resolved=True,
    ).delete()
    logger.info(
        "Cleanup: %d logs, %d resolved security events purged (>= %d days)",
        deleted_logs,
        deleted_security,
        days,
    )
    return {"logs": deleted_logs, "security": deleted_security}


@shared_task(name="monitor_endpoint_health")
def monitor_endpoint_health():
    """Check for endpoints that have been degraded > 1 hour and trigger alert."""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    degraded = APIEndpointStatus.objects.filter(
        is_degraded=True,
        degraded_since__lte=one_hour_ago,
    )
    for ep in degraded:
        SecurityEvent.objects.create(
            event_type=SecurityEvent.EventType.API_ABUSE,
            severity=SecurityEvent.Severity.CRITICAL,
            endpoint=ep.endpoint,
            details={
                "method": ep.method,
                "error_count": ep.error_count,
                "total_calls": ep.total_calls,
                "error_rate": round(ep.error_count / max(ep.total_calls, 1) * 100, 2),
                "avg_duration_ms": round(ep.avg_duration_ms, 1),
                "degraded_duration": str(timezone.now() - ep.degraded_since),
            },
            action_taken="Alerte dégradation endpoint générée",
        )
        logger.warning("Endpoint degraded >1h: %s %s", ep.method, ep.endpoint)

    count = degraded.count()
    logger.info("Endpoint health check: %d degraded endpoints alerted", count)
    return count
