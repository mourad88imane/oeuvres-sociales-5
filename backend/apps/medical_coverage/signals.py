from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.medical_coverage.models import MedicalCoverageVoucher


@receiver(post_save, sender=MedicalCoverageVoucher)
def check_eligibility_on_save(sender, instance, created, **kwargs):
    if created or instance.workflow_state in ("submitted", "approved"):
        from apps.medical_coverage.eligibility import EligibilityEngine
        engine = EligibilityEngine(MedicalCoverageVoucher)
        if instance.beneficiary_type == "dependent" and instance.beneficiary:
            result = engine.check_dependent_eligibility(
                instance.employee, instance.beneficiary,
                instance.coverage_type, instance.request_date,
            )
        else:
            result = engine.check_employee_eligibility(
                instance.employee, instance.coverage_type, instance.request_date,
            )
        instance.next_eligible_date = result.next_eligible_date
        if not created:
            MedicalCoverageVoucher.objects.filter(pk=instance.pk).update(
                next_eligible_date=result.next_eligible_date,
            )
