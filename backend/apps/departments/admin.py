from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Department

@admin.register(Department)
class DepartmentAdmin(SimpleHistoryAdmin):
    list_display  = ["code","name","parent","employee_count","is_active","created_at"]
    list_filter   = ["is_active","parent"]
    search_fields = ["code","name"]
    readonly_fields = ["id","created_at","updated_at","employee_count"]
