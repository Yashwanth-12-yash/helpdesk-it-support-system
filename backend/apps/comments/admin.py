from django.contrib import admin

from .models import TicketAttachment, TicketComment


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "is_internal", "created_at")
    list_filter = ("is_internal",)
    search_fields = ("ticket__ticket_number", "author__email", "body")


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "ticket", "uploaded_by", "file_size", "created_at")
    search_fields = ("original_filename", "ticket__ticket_number", "uploaded_by__email")
