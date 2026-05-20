"""Benefits Celery tasks."""
import logging
from celery import shared_task

logger = logging.getLogger("apps.benefits.tasks")

STATE_LABELS = {
    "submitted": "Soumise", "under_review": "En cours d'instruction",
    "on_hold": "En attente", "validated": "Validée",
    "paid": "Payée", "rejected": "Rejetée", "cancelled": "Annulée",
}

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_benefit_transition(self, benefit_id: str, to_state: str, actor_name: str, reason: str):
    """Notification asynchrone lors d'une transition de workflow."""
    try:
        from apps.benefits.models import Benefit
        from shared.notifications.models import Notification, NotificationPreference
        from shared.notifications.services import notification_service

        benefit = Benefit.objects.select_related(
            "employee", "benefit_type", "created_by"
        ).get(pk=benefit_id)

        label = STATE_LABELS.get(to_state, to_state)
        title = f"Prestation {label}"
        body = (
            f"La prestation {benefit.reference} ({benefit.benefit_type.name}) "
            f"est passée à l'état « {label} » par {actor_name}."
        )
        if reason:
            body += f" Motif : {reason}"

        priority = Notification.Priority.MEDIUM
        if to_state in ("validated", "paid"):
            priority = Notification.Priority.HIGH
        elif to_state in ("rejected", "cancelled"):
            priority = Notification.Priority.HIGH

        # Notify the employee who created the benefit
        if benefit.created_by:
            prefs, _ = NotificationPreference.objects.get_or_create(user=benefit.created_by)
            ch = Notification.Channel.EMAIL if prefs.email_alerts else Notification.Channel.IN_APP
            notification_service.send_notification(
                recipient=benefit.created_by,
                title=title,
                body=body,
                channel=ch,
                priority=priority,
                action_url=f"/benefits/{benefit.id}",
                icon="gift",
                instance=benefit,
            )

        # Also notify gestionnaires/admins for important transitions
        if to_state in ("submitted", "validated", "paid", "rejected"):
            notification_service.notify_gestionnaires(
                title=title,
                body=body,
                priority=priority,
                action_url=f"/benefits/{benefit.id}",
                icon="gift",
                instance=benefit,
            )

        logger.info("Notification envoyée: %s → %s", benefit.reference, to_state)
    except Exception as exc:
        logger.error("Notification failed for %s: %s", benefit_id, exc)
        raise self.retry(exc=exc)


@shared_task
def compute_benefit_scores():
    """Tâche périodique : calcul des scores AI (futur)."""
    logger.info("AI scoring task triggered — placeholder")
