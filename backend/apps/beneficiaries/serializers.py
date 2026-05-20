"""Beneficiary serializers."""
from rest_framework import serializers
from core.serializers import BaseModelSerializer
from .models import Beneficiary


class BeneficiarySerializer(BaseModelSerializer):
    full_name            = serializers.SerializerMethodField()
    age                  = serializers.ReadOnlyField()
    relationship_display = serializers.CharField(source="get_relationship_display", read_only=True)
    gender_display       = serializers.CharField(source="get_gender_display",       read_only=True)
    employee_name        = serializers.SerializerMethodField()

    class Meta:
        model  = Beneficiary
        fields = [
            "id","employee","employee_name","full_name","first_name","last_name",
            "first_name_ar","last_name_ar","gender","gender_display","date_of_birth","age",
            "national_id","relationship","relationship_display","is_eligible","ineligibility_reason",
            "is_student","is_handicapped","school_name","school_year",
            "spouse_is_employed","spouse_employer","birth_certificate_uploaded",
            "marriage_certificate_uploaded","notes","created_at","updated_at","created_by_name",
        ]
        read_only_fields = ["id","is_eligible","ineligibility_reason","created_at","updated_at"]

    def get_full_name(self, obj):     return obj.get_full_name()
    def get_employee_name(self, obj): return obj.employee.get_full_name()


class BeneficiaryCreateSerializer(BaseModelSerializer):
    class Meta:
        model  = Beneficiary
        fields = [
            "first_name","last_name","first_name_ar","last_name_ar","gender",
            "date_of_birth","national_id","relationship","is_student","is_handicapped",
            "school_name","school_year","spouse_is_employed","spouse_employer",
            "birth_certificate_uploaded","marriage_certificate_uploaded","notes",
        ]

    def validate_date_of_birth(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("La date de naissance doit être dans le passé.")
        return value

    def validate(self, attrs):
        employee = self.context.get("employee")
        if attrs.get("relationship") == Beneficiary.Relationship.SPOUSE and employee:
            existing = Beneficiary.objects.filter(
                employee=employee, relationship=Beneficiary.Relationship.SPOUSE, is_deleted=False
            ).exclude(pk=getattr(self.instance,"pk",None))
            if existing.exists():
                raise serializers.ValidationError({"relationship": "Un conjoint est déjà enregistré pour cet employé."})
        return attrs


class BeneficiaryUpdateSerializer(BaseModelSerializer):
    class Meta:
        model  = Beneficiary
        fields = [
            "first_name","last_name","first_name_ar","last_name_ar","gender",
            "date_of_birth","national_id","relationship","is_student","is_handicapped",
            "school_name","school_year","spouse_is_employed","spouse_employer",
            "birth_certificate_uploaded","marriage_certificate_uploaded","notes",
        ]
