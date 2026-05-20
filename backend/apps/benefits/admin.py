"""Benefits admin."""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Benefit, BenefitType, BenefitAttachment, BenefitComment

@admin.register(BenefitType)
class BenefitTypeAdmin(SimpleHistoryAdmin):
    list_display  = ["code","name","category","max_amount","min_seniority_years","is_active"]
    list_filter   = ["category","is_active"]
    search_fields = ["code","name"]

@admin.register(Benefit)
class BenefitAdmin(SimpleHistoryAdmin):
    list_display  = ["reference","benefit_type","employee","workflow_state","requested_amount","priority","submitted_at","ai_anomaly_flag"]
    list_filter   = ["workflow_state","priority","benefit_type__category","ai_anomaly_flag"]
    search_fields = ["reference","employee__first_name","employee__last_name","employee__matricule"]
    readonly_fields = ["id","reference","created_at","updated_at","workflow_updated_at"]

@admin.register(BenefitAttachment)
class BenefitAttachmentAdmin(admin.ModelAdmin):
    list_display = ["original_name","benefit","doc_type","file_size_display","uploaded_by","created_at"]
    list_filter  = ["doc_type"]

@admin.register(BenefitComment)
class BenefitCommentAdmin(admin.ModelAdmin):
    list_display = ["benefit","author","comment_type","created_at"]
    list_filter  = ["comment_type"]
