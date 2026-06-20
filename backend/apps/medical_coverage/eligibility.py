from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.translation import gettext as _


class EligibilityResult:
    def __init__(self):
        self.is_eligible = True
        self.messages = []
        self.next_eligible_date = None
        self.last_voucher_date = None
        self.last_voucher_reference = None
        self.count_last_3_months = 0
        self.count_current_year = 0
        self.remaining = 0

    def block(self, message: str, next_date: date = None):
        self.is_eligible = False
        self.messages.append(message)
        if next_date and (not self.next_eligible_date or next_date > self.next_eligible_date):
            self.next_eligible_date = next_date

    def add_warning(self, message: str):
        self.messages.append(message)


class EligibilityEngine:
    def __init__(self, voucher_model):
        self.Voucher = voucher_model

    def check_employee_eligibility(
        self, employee, coverage_type, request_date=None
    ) -> EligibilityResult:
        result = EligibilityResult()
        today = request_date or timezone.now().date()

        last_voucher = self.Voucher.objects.filter(
            employee=employee,
            coverage_type=coverage_type,
            beneficiary_type="employee",
            workflow_state__in=["approved", "consumed"],
        ).order_by("-request_date").first()

        if last_voucher:
            result.last_voucher_date = last_voucher.request_date
            result.last_voucher_reference = last_voucher.reference
            waiting_months = coverage_type.waiting_period_months
            next_allowed = last_voucher.request_date + relativedelta(months=waiting_months)

            if today < next_allowed:
                result.block(
                    _("L'employé a déjà consommé un bon au cours des {} derniers mois. "
                      "Prochaine date éligible : {}.").format(
                        waiting_months, next_allowed.strftime("%d/%m/%Y")
                    ),
                    next_date=next_allowed,
                )

        three_months_ago = today - relativedelta(months=3)
        result.count_last_3_months = self.Voucher.objects.filter(
            employee=employee,
            coverage_type=coverage_type,
            beneficiary_type="employee",
            workflow_state__in=["approved", "consumed"],
            request_date__gte=three_months_ago,
        ).count()

        year_start = date(today.year, 1, 1)
        result.count_current_year = self.Voucher.objects.filter(
            employee=employee,
            coverage_type=coverage_type,
            beneficiary_type="employee",
            workflow_state__in=["approved", "consumed"],
            request_date__gte=year_start,
        ).count()

        result.remaining = max(0, coverage_type.max_per_year - result.count_current_year)

        if result.count_current_year >= coverage_type.max_per_year:
            next_year_start = date(today.year + 1, 1, 1)
            result.block(
                _("L'employé a atteint le nombre maximum de bons pour l'année en cours."),
                next_date=next_year_start,
            )

        return result

    def check_dependent_eligibility(
        self, employee, dependent, coverage_type, request_date=None
    ) -> EligibilityResult:
        result = EligibilityResult()
        today = request_date or timezone.now().date()

        last_voucher = self.Voucher.objects.filter(
            employee=employee,
            beneficiary=dependent,
            coverage_type=coverage_type,
            workflow_state__in=["approved", "consumed"],
        ).order_by("-request_date").first()

        if last_voucher:
            result.last_voucher_date = last_voucher.request_date
            result.last_voucher_reference = last_voucher.reference
            waiting_months = coverage_type.waiting_period_months
            next_allowed = last_voucher.request_date + relativedelta(months=waiting_months)

            if today < next_allowed:
                result.block(
                    _("L'ayant droit a déjà consommé un bon au cours des {} derniers mois. "
                      "Prochaine date éligible : {}.").format(
                        waiting_months, next_allowed.strftime("%d/%m/%Y")
                    ),
                    next_date=next_allowed,
                )

        three_months_ago = today - relativedelta(months=3)
        result.count_last_3_months = self.Voucher.objects.filter(
            employee=employee,
            beneficiary=dependent,
            coverage_type=coverage_type,
            workflow_state__in=["approved", "consumed"],
            request_date__gte=three_months_ago,
        ).count()

        year_start = date(today.year, 1, 1)
        result.count_current_year = self.Voucher.objects.filter(
            employee=employee,
            beneficiary=dependent,
            coverage_type=coverage_type,
            workflow_state__in=["approved", "consumed"],
            request_date__gte=year_start,
        ).count()

        return result
