"""
Notifications Celery tasks.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger("shared.notifications.tasks")


@shared_task(name="send_notification_email", max_retries=3, default_retry_delay=60)
def send_notification_email(
    recipient_email: str,
    subject: str,
    body: str,
    html_body: str = "",
    priority: str = "medium",
    action_url: str = "",
    action_label: str = "",
    recipient_name: str = "",
):
    """
    Send a notification email asynchronously.
    Falls back to plain text if HTML rendering fails.
    """
    try:
        if html_body:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
        else:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        logger.info("Email sent to %s: %s", recipient_email, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", recipient_email, exc)
        raise send_notification_email.retry(exc=exc)


@shared_task(name="send_digest_emails")
def send_digest_emails():
    """
    Aggregate unread notifications and send digest emails.
    Runs daily/weekly based on user preferences.
    """
    from .models import Notification, NotificationPreference

    today = timezone.localdate()
    preferences = NotificationPreference.objects.filter(
        digest_frequency__in=["daily", "weekly"],
        email_alerts=True,
    ).select_related("user")

    sent = 0
    for pref in preferences:
        user = pref.user
        if not user.email:
            continue

        # Determine cutoff based on frequency
        if pref.digest_frequency == "daily":
            cutoff = today - timedelta(days=1)
        else:  # weekly
            cutoff = today - timedelta(days=7)

        unread = Notification.objects.filter(
            recipient=user, is_read=False, created_at__date__gte=cutoff,
        ).order_by("-created_at")

        if not unread.exists():
            continue

        lines = [
            f"- [{n.get_priority_display()}] {n.title}"
            for n in unread[:20]
        ]
        body = (
            f"Vous avez {unread.count()} notification(s) non lues "
            f"depuis le {cutoff} :\n\n"
            + "\n".join(lines)
            + f"\n\nConnectez-vous pour voir les détails."
        )

        send_notification_email.delay(
            recipient_email=user.email,
            subject=f"Récapitulatif — Œuvres Sociales ({pref.digest_frequency})",
            body=body,
            priority="medium",
            recipient_name=user.get_full_name() or user.email,
        )
        sent += 1

    logger.info("Digest emails sent: %d", sent)
    return sent


@shared_task(name="cleanup_old_notifications")
def cleanup_old_notifications(days=90):
    """Soft-delete read notifications older than `days`."""
    cutoff = timezone.now() - timedelta(days=days)
    qs = Notification.objects.filter(is_deleted=False, is_read=True, created_at__lt=cutoff)
    count = qs.count()
    for n in qs:
        n.soft_delete()
    logger.info("Cleaned up %d old notifications (>= %d days)", count, days)
    return count
