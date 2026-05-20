from django.db import models
from django.utils import timezone
from django.apps import apps
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.reporting.services import aggregation_service


class GlobalDashboardView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        months = int(request.query_params.get("months", 12))
        stats = aggregation_service.get_global_stats(user=request.user)
        trends = aggregation_service.get_monthly_trends(months=months)
        kpis = aggregation_service.get_all_kpis()
        top = aggregation_service.get_top_stats(limit=5)
        today = timezone.localdate()

        return Response({
            "status": "success",
            "data": {
                "kpis": kpis,
                "summary": stats,
                "trends": trends,
                "top": top,
                "date": today.isoformat(),
            },
        })
