"""
============================================================
DEPARTMENT SERVICE
============================================================
"""
import logging
from django.db import transaction
from shared.audit.services import AuditService
from .models import Department

logger = logging.getLogger("apps.departments")
audit  = AuditService()


class DepartmentService:

    @transaction.atomic
    def create(self, validated_data: dict, user=None, request=None) -> Department:
        dept = Department(**validated_data)
        if user:
            dept.created_by = user
            dept.updated_by = user
        dept.save()
        audit.log_create(user=user, obj=dept, request=request)
        return dept

    @transaction.atomic
    def update(self, dept: Department, validated_data: dict,
               user=None, request=None) -> Department:
        from django.forms.models import model_to_dict
        before = model_to_dict(dept)
        for attr, value in validated_data.items():
            setattr(dept, attr, value)
        if user:
            dept.updated_by = user
        dept.save()
        audit.log_update(user=user, obj=dept,
                         before_data=before, request=request)
        return dept

    @transaction.atomic
    def delete(self, dept: Department, user=None, request=None):
        # Vérifier qu'il n'y a pas d'employés actifs
        active_count = dept.employees.filter(
            status="active", is_deleted=False
        ).count()
        if active_count:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f"Impossible de supprimer : {active_count} employé(s) actif(s) dans ce département."
            )
        audit.log_delete(user=user, obj=dept, request=request)
        dept.soft_delete(user=user)
