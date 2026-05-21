"""
Reporting Celery tasks.
"""

import logging
from datetime import timedelta

from celery import shared_task

from django.utils import timezone

from .models import DataExport, ReportSchedule
from .services import aggregation_service

logger = logging.getLogger("apps.reporting.tasks")


@shared_task(name="snapshot_kpis")
def snapshot_kpis():
    """Compute and store a snapshot of all KPI values."""

    data = aggregation_service.compute_and_snapshot_kpis()
    count = len(data)
    logger.info("KPI snapshot completed: %d KPIs captured", count)
    return count


@shared_task(name="cleanup_old_exports")
def cleanup_old_exports(days=90):
    """Soft-delete exports older than `days`."""
    cutoff = timezone.now() - timedelta(days=days)
    qs = DataExport.objects.filter(is_deleted=False, created_at__lt=cutoff)
    count = qs.count()
    for export in qs:
        export.soft_delete()
    logger.info("Cleaned up %d old exports (>= %d days)", count, days)
    return count


@shared_task(name="generate_scheduled_reports")
def generate_scheduled_reports():
    """
    Check ReportSchedule entries whose next_run has passed
    and trigger generation for each.
    """
    now = timezone.now()
    schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run__lte=now,
        report__is_active=True,
    ).select_related("report")

    triggered = 0
    for schedule in schedules:
        report = schedule.report
        fmt = schedule.format or report.default_format
        from .views import ReportViewSet

        view = ReportViewSet()
        view.request = None  # will run with system-level context
        view.action = "generate"

        try:
            data = view._generate_report_data(report, schedule.filters_override or {})
            output = view._render_report(data, fmt, report)
            ext = "xlsx" if fmt == "excel" else fmt
            filename = f"{report.code}_scheduled_{now.strftime('%Y%m%d_%H%M%S')}.{ext}"

            export = DataExport.objects.create(
                report=report,
                export_format=fmt,
                status="completed",
                filters_used=schedule.filters_override or {},
                row_count=len(data),
                file_size=output.getbuffer().nbytes,
                completed_at=now,
            )
            export.file.save(filename, output, save=True)
            logger.info(
                "Scheduled report '%s' generated (format=%s, %d rows)",
                report.code,
                fmt,
                len(data),
            )
        except Exception as exc:
            DataExport.objects.create(
                report=report,
                export_format=fmt,
                status="failed",
                error_message=str(exc),
                filters_used=schedule.filters_override or {},
            )
            logger.exception("Scheduled report '%s' failed", report.code)

        # Update schedule for next run
        schedule.last_run = now
        if schedule.cron_expression:
            from croniter import croniter

            base = now.replace(second=0, microsecond=0)
            it = croniter(schedule.cron_expression, base)
            schedule.next_run = it.get_next(ret_type=type(now))
        else:
            schedule.next_run = now + timedelta(days=1)
        schedule.save(update_fields=["last_run", "next_run", "updated_at"])
        triggered += 1

    logger.info("generate_scheduled_reports: %d reports triggered", triggered)
    return triggered
