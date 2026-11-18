from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable audit log of security-sensitive and administrative actions."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_email = models.CharField(max_length=255, blank=True, default="")
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=64, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_auditlog"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["resource_type", "resource_id"], name="idx_audit_resource"),
            models.Index(fields=["actor", "created_at"], name="idx_audit_actor_created"),
            models.Index(fields=["action", "created_at"], name="idx_audit_action_created"),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.actor_email} - {self.action} ({self.resource_type}:{self.resource_id})"
