from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app and email-backed notification for ticket & SLA events."""

    class EventType(models.TextChoices):
        TICKET_CREATED = "TICKET_CREATED", "Ticket Created"
        TICKET_ASSIGNED = "TICKET_ASSIGNED", "Ticket Assigned"
        TICKET_REASSIGNED = "TICKET_REASSIGNED", "Ticket Reassigned"
        STATUS_CHANGED = "STATUS_CHANGED", "Status Changed"
        COMMENT_ADDED = "COMMENT_ADDED", "Comment Added"
        SLA_WARNING = "SLA_WARNING", "SLA Approaching Deadline"
        SLA_BREACHED = "SLA_BREACHED", "SLA Breached"
        TICKET_RESOLVED = "TICKET_RESOLVED", "Ticket Resolved"
        TICKET_REOPENED = "TICKET_REOPENED", "Ticket Reopened"
        ESCALATED = "ESCALATED", "Ticket Escalated"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "created_at"], name="idx_notif_recip_read"),
        ]

    def __str__(self):
        return f"Notification({self.recipient.email}, {self.event_type})"
