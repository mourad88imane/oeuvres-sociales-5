"""Finance admin."""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import FiscalYear, Budget, Payment, PaymentBatch, FinancialEntry, FinancialAlert

@admin.register(FiscalYear)
class FiscalYearAdmin(SimpleHistoryAdmin):
    list_display = ["year","label","status","total_budget","total_paid","consumption_rate","is_active"]
    list_filter  = ["status"]

@admin.register(Budget)
class BudgetAdmin(SimpleHistoryAdmin):
    list_display = ["code","label","fiscal_year","benefit_type","allocated_amount","paid_amount","consumption_rate","status","is_alert_triggered"]
    list_filter  = ["status","fiscal_year"]
    search_fields= ["code","label"]

@admin.register(Payment)
class PaymentAdmin(SimpleHistoryAdmin):
    list_display = ["reference","employee","amount","status","payment_method","executed_date","anomaly_flag"]
    list_filter  = ["status","anomaly_flag","fiscal_year"]
    search_fields= ["reference","employee__first_name","employee__last_name"]
    readonly_fields = ["id","reference","created_at","updated_at"]

@admin.register(PaymentBatch)
class PaymentBatchAdmin(SimpleHistoryAdmin):
    list_display = ["reference","label","total_amount","payment_count","status","scheduled_date"]
    list_filter  = ["status"]

@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = ["entry_number","entry_type","label","amount","entry_date"]
    list_filter  = ["entry_type","fiscal_year"]
    readonly_fields = [f.name for f in FinancialEntry._meta.get_fields() if hasattr(f,"name")]
    def has_add_permission(self, r):    return False
    def has_change_permission(self, r, obj=None): return False

@admin.register(FinancialAlert)
class FinancialAlertAdmin(admin.ModelAdmin):
    list_display = ["title","alert_type","severity","is_resolved","ai_generated","created_at"]
    list_filter  = ["severity","alert_type","is_resolved","ai_generated"]
