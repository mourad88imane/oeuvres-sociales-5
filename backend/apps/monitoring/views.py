import logging
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import APIRequestLog, SecurityEvent, BusinessMetric, APIEndpointStatus
from .serializers import (
    APIRequestLogSerializer, SecurityEventSerializer, ResolveSecurityEventSerializer,
    APIEndpointStatusSerializer, DashboardStatsSerializer, BusinessMetricSerializer,
)
from .services import monitoring_service

logger = logging.getLogger("apps.monitoring")


class MonitoringViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        hours = int(request.query_params.get("hours", 24))
        stats = monitoring_service.get_dashboard_stats(hours=hours)
        return Response({"status": "success", "data": stats})

    @action(detail=False, methods=["get"])
    def api_logs(self, request):
        is_error = request.query_params.get("is_error")
        if is_error is not None:
            is_error = is_error.lower() == "true"
        logs = monitoring_service.get_api_logs(
            limit=int(request.query_params.get("limit", 100)),
            is_error=is_error,
            method=request.query_params.get("method"),
            endpoint=request.query_params.get("endpoint"),
            days=int(request.query_params.get("days", 7)),
        )
        serializer = APIRequestLogSerializer(logs, many=True)
        return Response({"status": "success", "data": serializer.data})

    @action(detail=False, methods=["get"])
    def security_events(self, request):
        events = monitoring_service.get_security_events(
            limit=int(request.query_params.get("limit", 50)),
            severity=request.query_params.get("severity"),
            resolved=request.query_params.get("resolved"),
        )
        serializer = SecurityEventSerializer(events, many=True)
        return Response({"status": "success", "data": serializer.data})

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        try:
            event = SecurityEvent.objects.get(pk=pk)
        except SecurityEvent.DoesNotExist:
            return Response(
                {"status": "error", "message": "Événement non trouvé"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResolveSecurityEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event.resolved = True
        event.resolved_at = timezone.now()
        event.resolved_by = request.user
        event.resolution_note = serializer.validated_data.get("resolution_note", "")
        event.save(update_fields=["resolved", "resolved_at", "resolved_by", "resolution_note"])

        return Response({"status": "success", "data": {"id": str(event.pk), "resolved": True}})

    @action(detail=False, methods=["get"])
    def endpoint_status(self, request):
        statuses = monitoring_service.get_endpoint_statuses()
        serializer = APIEndpointStatusSerializer(statuses, many=True)
        return Response({"status": "success", "data": serializer.data})

    @action(detail=False, methods=["get"])
    def audit_summary(self, request):
        days = int(request.query_params.get("days", 30))
        summary = monitoring_service.get_audit_summary(days=days)
        return Response({"status": "success", "data": summary})

    @action(detail=False, methods=["get"])
    def metrics(self, request):
        metric_type = request.query_params.get("metric_type")
        hours = int(request.query_params.get("hours", 24))
        since = timezone.now() - timedelta(hours=hours)
        qs = BusinessMetric.objects.filter(timestamp__gte=since)
        if metric_type:
            qs = qs.filter(metric_type=metric_type)
        qs = qs.order_by("-timestamp")[:200]
        serializer = BusinessMetricSerializer(qs, many=True)
        return Response({"status": "success", "data": serializer.data})
