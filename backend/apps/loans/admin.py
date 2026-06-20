from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Loan, LoanAttachment, LoanComment


@admin.register(Loan)
class LoanAdmin(SimpleHistoryAdmin):
    list_display = [
        "reference", "employee", "workflow_state", "requested_amount",
        "submitted_at", "validated_at",
    ]
    list_filter = ["workflow_state"]
    search_fields = ["reference", "employee__first_name", "employee__last_name", "employee__matricule"]
    readonly_fields = ["id", "reference", "created_at", "updated_at", "workflow_updated_at"]


@admin.register(LoanAttachment)
class LoanAttachmentAdmin(admin.ModelAdmin):
    list_display = ["original_name", "loan", "doc_type", "file_size_display", "uploaded_by", "created_at"]
    list_filter = ["doc_type"]


@admin.register(LoanComment)
class LoanCommentAdmin(admin.ModelAdmin):
    list_display = ["loan", "author", "comment_type", "created_at"]
    list_filter = ["comment_type"]
