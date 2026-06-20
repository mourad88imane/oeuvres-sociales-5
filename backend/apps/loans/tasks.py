import logging

from celery import shared_task

logger = logging.getLogger("apps.loans.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_loan_transition(self, loan_id, to_state, actor_name, reason):
    try:
        from .models import Loan
        loan = Loan.objects.get(pk=loan_id)
        logger.info(
            f"Notification: Prêt {loan.reference} → {to_state} par {actor_name}",
            extra={"loan_id": loan_id, "to_state": to_state, "reason": reason},
        )
    except Exception as e:
        logger.warning(f"Notification task failed: {e}")
