import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger("apps.benefits.signals")


def wire_benefit_signals():
    """Connect benefit AI signals — called from apps.ready() to avoid import issues."""
    from .models import Benefit

    @receiver(post_save, sender=Benefit, weak=False, dispatch_uid="benefit_ai_scoring")
    def benefit_ai_scoring(sender, instance, created, **kwargs):
        """Trigger AI scoring and pipeline when a benefit is saved."""
        try:
            from shared.ai.pipeline import AIPipeline
            from shared.ai.scoring import ScoringEngine

            scoring = ScoringEngine()
            pipeline = AIPipeline()

            scoring.score_benefit(str(instance.pk), save=True)
            pipeline.run_benefit_pipeline(benefit_id=str(instance.pk))
        except Exception as e:
            logger.exception("AI scoring failed for benefit %s: %s", instance.pk, e)
