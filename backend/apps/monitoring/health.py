import logging
from datetime import datetime, timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger("apps.monitoring")


@api_view(["GET"])
@permission_classes([AllowAny])
def liveness(request):
    """Liveness probe — return 200 if the app is running."""
    return Response({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness(request):
    """Readiness probe — check DB and Redis connectivity."""
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
    }
    all_healthy = all(check.get("healthy") for check in checks.values())
    status_code = 200 if all_healthy else 503
    return Response({
        "status": "ok" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
def deep_health(request):
    """Deep health check — full system status including Celery."""
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
        "celery": _check_celery(),
    }
    all_healthy = all(check.get("healthy") for check in checks.values())
    status_code = 200 if all_healthy else 503
    return Response({
        "status": "ok" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "checks": checks,
    }, status=status_code)


def _check_database():
    try:
        conn = connections["default"]
        conn.ensure_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"healthy": True, "message": "Database connected"}
    except OperationalError as e:
        logger.error("Health check — database failed: %s", e)
        return {"healthy": False, "message": str(e)}


def _check_cache():
    try:
        from django.core.cache import cache
        cache.set("__health__", 1, timeout=5)
        result = cache.get("__health__")
        return {"healthy": result == 1, "message": "Cache reachable" if result == 1 else "Cache read failed"}
    except Exception as e:
        logger.error("Health check — cache failed: %s", e)
        return {"healthy": False, "message": str(e)}


def _check_celery():
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        workers = list(stats.keys()) if stats else []
        return {
            "healthy": len(workers) > 0,
            "message": f"Celery workers: {len(workers)}" if workers else "No Celery workers detected",
            "workers": workers,
        }
    except Exception as e:
        logger.error("Health check — celery failed: %s", e)
        return {"healthy": False, "message": str(e)}
