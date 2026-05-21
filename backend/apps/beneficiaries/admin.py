from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Beneficiary


@admin.register(Beneficiary)
class BeneficiaryAdmin(SimpleHistoryAdmin):
    list_display = ["get_full_name", "employee", "relationship", "age", "is_eligible", "is_deleted"]
    list_filter = ["relationship", "is_eligible", "gender"]
    search_fields = ["first_name", "last_name", "employee__matricule"]
    readonly_fields = ["id", "is_eligible", "ineligibility_reason", "created_at", "updated_at"]
