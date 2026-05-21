from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(SimpleHistoryAdmin):
    list_display = [
        "matricule",
        "get_full_name",
        "department",
        "job_title",
        "status",
        "date_hired",
        "created_at",
    ]
    list_filter = ["status", "gender", "department", "contract_type"]
    search_fields = ["matricule", "first_name", "last_name", "national_id", "email_professional"]
    readonly_fields = ["id", "matricule", "created_at", "updated_at", "age", "seniority_label"]
    fieldsets = (
        (
            "Identification",
            {
                "fields": (
                    "matricule",
                    "first_name",
                    "last_name",
                    "first_name_ar",
                    "last_name_ar",
                    "gender",
                    "date_of_birth",
                    "nationality",
                    "marital_status",
                )
            },
        ),
        (
            "Documents",
            {"fields": ("national_id", "national_id_expiry", "social_security_number", "tax_id")},
        ),
        (
            "Contact",
            {
                "fields": (
                    "phone",
                    "phone_secondary",
                    "email_personal",
                    "email_professional",
                    "address",
                    "city",
                    "wilaya",
                )
            },
        ),
        ("Photo", {"fields": ("photo",)}),
        (
            "Poste",
            {
                "fields": (
                    "department",
                    "job_title",
                    "grade",
                    "grade_level",
                    "category",
                    "contract_type",
                    "manager",
                    "status",
                )
            },
        ),
        ("Dates RH", {"fields": ("date_hired", "date_end", "date_retired", "date_promoted")}),
        ("Finance", {"fields": ("base_salary", "bank_account")}),
        ("Formation", {"fields": ("education_level", "education_field")}),
        (
            "AI / Analytics",
            {"fields": ("competencies", "scoring_profile", "metadata"), "classes": ("collapse",)},
        ),
        ("Notes", {"fields": ("notes",)}),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
