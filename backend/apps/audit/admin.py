from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_email", "action", "resource_type", "resource_id", "ip_address")
    list_filter = ("action", "resource_type")
    search_fields = ("actor_email", "resource_id", "action")
    readonly_fields = (
        "actor",
        "actor_email",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "user_agent",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
