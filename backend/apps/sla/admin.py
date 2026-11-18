from django.contrib import admin

from .models import Escalation, SLAPolicy, TicketSLA


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "priority",
        "department",
        "first_response_minutes",
        "resolution_minutes",
        "business_hours_only",
        "is_active",
    )
    list_filter = ("priority", "business_hours_only", "is_active")


@admin.register(TicketSLA)
class TicketSLAAdmin(admin.ModelAdmin):
    list_display = (
        "ticket",
        "policy",
        "response_due_at",
        "resolution_due_at",
        "response_breached",
        "resolution_breached",
    )
    list_filter = ("response_breached", "resolution_breached")


@admin.register(Escalation)
class EscalationAdmin(admin.ModelAdmin):
    list_display = ("ticket", "escalation_type", "escalated_to", "is_acknowledged", "created_at")
    list_filter = ("escalation_type", "is_acknowledged")
