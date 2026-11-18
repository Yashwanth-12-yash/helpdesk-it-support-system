from django.contrib import admin

from .models import Ticket, TicketHistory


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ("changed_by", "action_type", "field_name", "old_value", "new_value", "note", "created_at")
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "title",
        "priority",
        "status",
        "department",
        "assigned_engineer",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "department")
    search_fields = ("ticket_number", "title", "description", "created_by__email")
    readonly_fields = ("ticket_number", "created_at", "updated_at", "first_responded_at", "resolved_at", "closed_at")
    inlines = [TicketHistoryInline]
