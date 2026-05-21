import logging

from celery import shared_task

from django.utils import timezone
from shared.notifications.models import Notification
from shared.notifications.services import notification_service

from .models import Convention, ConventionAlert

logger = logging.getLogger("apps.conventions.tasks")


@shared_task(name="check_convention_expirations")
def check_convention_expirations():
    today = timezone.localdate()
    warnings = []
    expirations = []
    reminders = []

    active_convs = Convention.objects.filter(
        is_deleted=False,
        status__in=[Convention.Status.ACTIVE, Convention.Status.EXPIRING_SOON],
    )

    for conv in active_convs.select_related("partner"):
        if not conv.end_date:
            continue
        delta = (conv.end_date - today).days

        if delta <= 0:
            conv.status = Convention.Status.EXPIRED
            conv.save(update_fields=["status", "updated_at"])
            expirations.append(conv)
            alert = ConventionAlert.objects.create(
                convention=conv,
                alert_type=ConventionAlert.AlertType.EXPIRY_CRITICAL,
                severity=ConventionAlert.Severity.CRITICAL,
                title="Convention expirée",
                message=f"La convention {conv.reference} ({conv.partner.name}) est arrivée à expiration.",
            )
            notification_service.notify_admins(
                title="Convention expirée",
                body=f"La convention {conv.reference} ({conv.partner.name}) est arrivée à expiration.",
                priority=Notification.Priority.CRITICAL,
                action_url=f"/conventions/{conv.id}",
                icon="alert-triangle",
                instance=alert,
            )
            logger.warning("Convention expirée: %s", conv.reference)

        elif delta <= 7:
            if not ConventionAlert.objects.filter(
                convention=conv,
                alert_type=ConventionAlert.AlertType.EXPIRY_CRITICAL,
                is_resolved=False,
            ).exists():
                alert = ConventionAlert.objects.create(
                    convention=conv,
                    alert_type=ConventionAlert.AlertType.EXPIRY_CRITICAL,
                    severity=ConventionAlert.Severity.CRITICAL,
                    title="Expiration imminente",
                    message=f"La convention {conv.reference} expire dans {delta} jour(s) ({conv.end_date}).",
                )
                notification_service.notify_admins(
                    title="Expiration imminente",
                    body=f"La convention {conv.reference} expire dans {delta} jour(s) ({conv.end_date}).",
                    priority=Notification.Priority.HIGH,
                    action_url=f"/conventions/{conv.id}",
                    icon="clock",
                    instance=alert,
                )
            warnings.append(conv)

        elif delta <= 30:
            if not ConventionAlert.objects.filter(
                convention=conv,
                alert_type=ConventionAlert.AlertType.EXPIRY_WARNING,
                is_resolved=False,
            ).exists():
                ConventionAlert.objects.create(
                    convention=conv,
                    alert_type=ConventionAlert.AlertType.EXPIRY_WARNING,
                    severity=ConventionAlert.Severity.HIGH,
                    title="Expiration prochaine",
                    message=f"La convention {conv.reference} expire dans {delta} jour(s) ({conv.end_date}).",
                )
                notification_service.notify_admins(
                    title="Expiration prochaine",
                    body=f"La convention {conv.reference} expire dans {delta} jour(s) ({conv.end_date}).",
                    priority=Notification.Priority.MEDIUM,
                    action_url=f"/conventions/{conv.id}",
                    icon="bell",
                )
            warnings.append(conv)

        if delta <= conv.renewal_notice_days and conv.renewal_mode != Convention.Renewal.NONE:
            if not ConventionAlert.objects.filter(
                convention=conv,
                alert_type=ConventionAlert.AlertType.RENEWAL_REMINDER,
                is_resolved=False,
            ).exists():
                ConventionAlert.objects.create(
                    convention=conv,
                    alert_type=ConventionAlert.AlertType.RENEWAL_REMINDER,
                    severity=ConventionAlert.Severity.MEDIUM,
                    title="Rappel reconduction",
                    message=f"Préavis de reconduction pour {conv.reference} (échéance: {conv.end_date}).",
                )
            reminders.append(conv)

    logger.info(
        "check_convention_expirations terminé: %d expirées, %d alertes, %d rappels",
        len(expirations),
        len(warnings),
        len(reminders),
    )
    return {
        "expired": len(expirations),
        "warnings": len(warnings),
        "reminders": len(reminders),
    }
