import logging
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import APIRequestLog, SecurityEvent, BusinessMetric, APIEndpointStatus

logger = logging.getLogger("apps.monitoring")


class MonitoringService:
    def get_dashboard_stats(self, hours=24):
        since = timezone.now() - timedelta(hours=hours)
        recent = APIRequestLog.objects.filter(timestamp__gte=since)

        total_calls = recent.count()
        errors = recent.filter(is_error=True).count()
        avg_duration = recent.aggregate(avg=Avg("duration_ms"))["avg"] or 0

        top_endpoints = list(
            recent.values("endpoint", "method")
            .annotate(count=Count("id"), avg_dur=Avg("duration_ms"), err_count=Count("id", filter=Q(is_error=True)))
            .order_by("-count")[:10]
        )

        calls_by_hour = list(
            recent.extra({"hour": "date_trunc('hour', timestamp)"})
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        security_alerts = SecurityEvent.objects.filter(
            timestamp__gte=since, severity__in=["HIGH", "CRITICAL"],
        ).count()

        degraded_endpoints = APIEndpointStatus.objects.filter(is_degraded=True).count()

        user_counts = list(
            recent.exclude(user__isnull=True)
            .values("user__email")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return {
            "total_calls": total_calls,
            "errors": errors,
            "error_rate": round(errors / max(total_calls, 1) * 100, 2),
            "avg_duration_ms": round(avg_duration, 1),
            "top_endpoints": top_endpoints,
            "calls_by_hour": calls_by_hour,
            "security_alerts": security_alerts,
            "degraded_endpoints": degraded_endpoints,
            "top_users": user_counts,
        }

    def get_security_events(self, limit=50, severity=None, resolved=None):
        qs = SecurityEvent.objects.all()
        if severity:
            qs = qs.filter(severity=severity)
        if resolved is not None:
            qs = qs.filter(resolved=resolved)
        return qs.order_by("-timestamp")[:limit]

    def get_api_logs(self, limit=100, is_error=None, method=None, endpoint=None, days=7):
        since = timezone.now() - timedelta(days=days)
        qs = APIRequestLog.objects.filter(timestamp__gte=since)
        if is_error is not None:
            qs = qs.filter(is_error=is_error)
        if method:
            qs = qs.filter(method=method.upper())
        if endpoint:
            qs = qs.filter(endpoint__icontains=endpoint)
        return qs.order_by("-timestamp")[:limit]

    def get_endpoint_statuses(self):
        return APIEndpointStatus.objects.filter().order_by("-total_calls")

    def get_audit_summary(self, days=30):
        from shared.audit.models import AuditLog
        since = timezone.now() - timedelta(days=days)
        qs = AuditLog.objects.filter(timestamp__gte=since)

        total = qs.count()
        by_action = list(
            qs.values("action").annotate(count=Count("id")).order_by("-count")
        )
        by_severity = list(
            qs.values("severity").annotate(count=Count("id")).order_by("severity")
        )
        top_users = list(
            qs.values("user_email").annotate(count=Count("id")).order_by("-count")[:10]
        )

        return {
            "total": total,
            "by_action": by_action,
            "by_severity": by_severity,
            "top_users": top_users,
        }

    def record_business_metric(self, metric_type, value, label="", tags=None, granularity="1h"):
        BusinessMetric.objects.create(
            metric_type=metric_type,
            granularity=granularity,
            value=value,
            label=label,
            tags=tags or {},
            timestamp=timezone.now(),
        )


monitoring_service = MonitoringService()
