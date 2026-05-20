"""
============================================================
EMPLOYEE SERVICE — Logique métier découplée des vues
============================================================
PRINCIPE : Les vues ne contiennent que du code HTTP.
Toute la logique métier est ici, testable unitairement.

Ce service est aussi le point d'intégration futur pour :
- Le moteur de scoring AI
- Les recommandations
- Les alertes automatiques
"""
import logging
from typing import Optional

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q, QuerySet

from shared.audit.services import AuditService
from .models import Employee

logger = logging.getLogger("apps.employees")
audit = AuditService()


class EmployeeService:
    """
    Service de gestion des employés.
    Toutes les opérations CRUD + métier passent par ici.
    """

    # ── Requêtes ─────────────────────────────────────────
    def get_queryset(self) -> QuerySet:
        """QuerySet de base avec les relations nécessaires."""
        return (
            Employee.objects
            .select_related("department", "manager")
            .prefetch_related("beneficiaries")
        )

    def search(
        self,
        queryset: QuerySet,
        search_term: str = "",
        status: str = "",
        department_id: str = "",
        contract_type: str = "",
        gender: str = "",
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_seniority: Optional[float] = None,
        grade_level: Optional[int] = None,
        ordering: str = "-created_at",
    ) -> QuerySet:
        """
        Recherche et filtrage avancé des employés.
        Supporte la recherche full-text sur plusieurs champs.
        """
        if search_term:
            queryset = queryset.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(matricule__icontains=search_term) |
                Q(email_professional__icontains=search_term) |
                Q(job_title__icontains=search_term) |
                Q(national_id__icontains=search_term)
            )

        if status:
            queryset = queryset.filter(status=status)

        if department_id:
            queryset = queryset.filter(department_id=department_id)

        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)

        if gender:
            queryset = queryset.filter(gender=gender)

        if grade_level is not None:
            queryset = queryset.filter(grade_level=grade_level)

        # Filtres sur âge — calculés via date_of_birth
        if min_age is not None:
            from datetime import date
            from dateutil.relativedelta import relativedelta
            max_dob = date.today() - relativedelta(years=min_age)
            queryset = queryset.filter(date_of_birth__lte=max_dob)

        if max_age is not None:
            from datetime import date
            from dateutil.relativedelta import relativedelta
            min_dob = date.today() - relativedelta(years=max_age + 1)
            queryset = queryset.filter(date_of_birth__gte=min_dob)

        # Filtre ancienneté (en années)
        if min_seniority is not None:
            from datetime import date, timedelta
            max_hire_date = date.today() - timedelta(days=int(min_seniority * 365.25))
            queryset = queryset.filter(date_hired__lte=max_hire_date)

        # Ordering sécurisé (whitelist)
        allowed_orderings = {
            "last_name", "-last_name", "first_name", "-first_name",
            "matricule", "-matricule", "date_hired", "-date_hired",
            "date_of_birth", "-date_of_birth", "status", "-status",
            "created_at", "-created_at", "grade_level", "-grade_level",
        }
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)

        return queryset

    # ── CRUD ─────────────────────────────────────────────
    @transaction.atomic
    def create(self, validated_data: dict, user=None, request=None) -> Employee:
        """Crée un employé avec audit log."""
        photo = validated_data.pop("photo", None)
        employee = Employee(**validated_data)
        if user:
            employee.created_by = user
            employee.updated_by = user
        employee.save()

        if photo:
            employee.photo = photo
            employee.save(update_fields=["photo"])

        audit.log_create(user=user, obj=employee, request=request)
        logger.info("Employee created", extra={
            "employee_id": str(employee.id),
            "matricule": employee.matricule,
            "by": str(user.id) if user else "system",
        })
        return employee

    @transaction.atomic
    def update(
        self,
        employee: Employee,
        validated_data: dict,
        user=None,
        request=None,
        partial: bool = False,
    ) -> Employee:
        """Met à jour un employé avec audit log (avant/après)."""
        from django.forms.models import model_to_dict
        before_data = model_to_dict(employee, exclude=["photo", "password"])

        photo = validated_data.pop("photo", None)

        for attr, value in validated_data.items():
            setattr(employee, attr, value)

        if user:
            employee.updated_by = user
        employee.save()

        if photo:
            # Supprimer l'ancienne photo
            if employee.photo:
                employee.photo.delete(save=False)
            employee.photo = photo
            employee.save(update_fields=["photo", "updated_at"])

        audit.log_update(
            user=user, obj=employee,
            before_data=before_data, request=request,
        )
        logger.info("Employee updated", extra={
            "employee_id": str(employee.id),
            "matricule": employee.matricule,
        })
        return employee

    @transaction.atomic
    def delete(self, employee: Employee, user=None, request=None):
        """Soft delete avec audit log."""
        audit.log_delete(user=user, obj=employee, request=request)
        employee.soft_delete(user=user)
        logger.warning("Employee deleted (soft)", extra={
            "employee_id": str(employee.id),
            "matricule": employee.matricule,
        })

    def upload_photo(self, employee: Employee, photo, user=None, request=None) -> Employee:
        """Upload/remplacement de la photo avec validation."""
        # Supprimer l'ancienne photo du stockage
        if employee.photo:
            employee.photo.delete(save=False)

        employee.photo = photo
        if user:
            employee.updated_by = user
        employee.save(update_fields=["photo", "updated_at", "updated_by"])

        audit.log_action(
            action="UPDATE",
            user=user,
            obj=employee,
            request=request,
            extra_data={"field": "photo", "action": "upload"},
        )
        return employee

    def delete_photo(self, employee: Employee, user=None, request=None) -> Employee:
        """Suppression de la photo."""
        if employee.photo:
            employee.photo.delete(save=False)
            employee.photo = None
            if user:
                employee.updated_by = user
            employee.save(update_fields=["photo", "updated_at", "updated_by"])
        return employee

    # ── Statistiques (préparation dashboard / AI) ────────
    def get_statistics(self) -> dict:
        """
        Statistiques agrégées des employés.
        Utilisées par le dashboard et futures analytics AI.
        """
        from django.db.models import Count, Avg
        from datetime import date

        qs = Employee.objects.filter(is_deleted=False)

        stats = {
            "total": qs.count(),
            "by_status": list(
                qs.values("status").annotate(count=Count("id")).order_by("status")
            ),
            "by_department": list(
                qs.filter(status=Employee.Status.ACTIVE)
                .values("department__name", "department__code")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
            "by_contract_type": list(
                qs.values("contract_type").annotate(count=Count("id"))
            ),
            "by_gender": list(
                qs.values("gender").annotate(count=Count("id"))
            ),
            "active_count": qs.filter(status=Employee.Status.ACTIVE).count(),
            "retired_count": qs.filter(status=Employee.Status.RETIRED).count(),
            "new_this_year": qs.filter(
                date_hired__year=date.today().year
            ).count(),
        }

        # Calcul ancienneté moyenne (en années)
        active = qs.filter(status=Employee.Status.ACTIVE, date_hired__isnull=False)
        if active.exists():
            from django.db.models import ExpressionWrapper, F, DurationField
            from django.utils import timezone as tz
            import datetime
            avg_days = (
                active
                .annotate(
                    tenure=ExpressionWrapper(
                        tz.now().date() - F("date_hired"),
                        output_field=DurationField(),
                    )
                )
                .aggregate(avg=Avg("tenure"))["avg"]
            )
            if avg_days:
                stats["avg_seniority_years"] = round(avg_days.days / 365.25, 1)
            else:
                stats["avg_seniority_years"] = 0
        else:
            stats["avg_seniority_years"] = 0

        return stats

    # ── Validation métier ────────────────────────────────
    def validate_business_rules(self, data: dict, instance: Employee = None) -> list:
        """
        Valide les règles métier avant création/mise à jour.
        Retourne une liste d'erreurs (vide = valide).

        Séparé du serializer pour être testable indépendamment.
        """
        errors = []
        from datetime import date

        # Date embauche ne peut pas être dans le futur
        date_hired = data.get("date_hired")
        if date_hired and date_hired > date.today():
            errors.append("La date d'embauche ne peut pas être dans le futur.")

        # Age minimum d'embauche
        dob = data.get("date_of_birth")
        if dob and date_hired:
            age_at_hiring = (date_hired - dob).days // 365
            if age_at_hiring < 16:
                errors.append("L'employé doit avoir au moins 16 ans à la date d'embauche.")

        # Date de fin > date d'embauche
        date_end = data.get("date_end")
        if date_end and date_hired and date_end <= date_hired:
            errors.append("La date de fin de contrat doit être postérieure à la date d'embauche.")

        return errors
