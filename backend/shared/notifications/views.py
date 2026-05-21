"""Notification API views."""

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.pagination import StandardResultsSetPagination
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Notification, NotificationPreference
from .serializers import (
    MarkReadSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)

logger = logging.getLogger("shared.notifications")


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(
            recipient=self.request.user,
            is_deleted=False,
        ).order_by("-created_at")

        # Filters
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")

        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        channel = self.request.query_params.get("channel")
        if channel:
            qs = qs.filter(channel=channel)

        return qs

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            is_deleted=False,
        ).count()
        high = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            is_deleted=False,
            priority__in=[Notification.Priority.HIGH, Notification.Priority.CRITICAL],
        ).count()
        return Response({"status": "success", "data": {"count": count, "high_priority": high}})

    @action(detail=False, methods=["post"])
    def mark_read(self, request):
        ser = MarkReadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        if ser.validated_data.get("all"):
            qs = Notification.objects.filter(
                recipient=request.user,
                is_read=False,
                is_deleted=False,
            )
            count = qs.count()
            qs.update(is_read=True, read_at=timezone.now())
            logger.info("%d notifications marquées lues pour %s", count, request.user)
            return Response({"status": "success", "marked_read": count})

        ids = ser.validated_data.get("ids", [])
        if ids:
            qs = Notification.objects.filter(
                id__in=ids,
                recipient=request.user,
                is_deleted=False,
            )
            count = qs.count()
            qs.update(is_read=True, read_at=timezone.now())
            return Response({"status": "success", "marked_read": count})

        return Response({"status": "success", "marked_read": 0})

    @action(detail=True, methods=["post"])
    def mark_one_read(self, request, pk=None):
        try:
            notif = Notification.objects.get(id=pk, recipient=request.user, is_deleted=False)
            notif.mark_as_read()
            return Response({"status": "success"})
        except Notification.DoesNotExist:
            return Response(
                {"status": "error", "message": _("Notification introuvable")},
                status=status.HTTP_404_NOT_FOUND,
            )


class NotificationPreferenceViewSet(viewsets.GenericViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj

    @action(detail=False, methods=["get", "put", "patch"])
    def my_preferences(self, request):
        prefs = self.get_object()
        if request.method == "GET":
            ser = self.get_serializer(prefs)
            return Response({"status": "success", "data": ser.data})
        ser = self.get_serializer(prefs, data=request.data, partial=request.method == "PATCH")
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"status": "success", "data": ser.data})
