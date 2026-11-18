from datetime import time
from django.conf import settings
from django.db import models

from apps.tickets.models import Ticket


def default_working_days():
    return [0, 1, 2, 3, 4]  # Monday - Friday


class SLAPolicy(models.Model):
    """Configurable priority-based (and optional department-specific) SLA policy."""

    name = models.CharField(max_length=120)
    priority = models.CharField(max_length=20, choices=Ticket.Priority.choices, db_index=True)
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sla_policies",
    )
    first_response_minutes = models.PositiveIntegerField()
    resolution_minutes = models.PositiveIntegerField()
    escalation_threshold_pct = models.PositiveSmallIntegerField(default=80)

    business_hours_only = models.BooleanField(default=False)
    business_start_time = models.TimeField(default=time(9, 0))
    business_end_time = models.TimeField(default=time(18, 0))
    working_days = models.JSONField(default=default_working_days)

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sla_slapolicy"
        ordering = ["priority", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["priority", "department"],
                name="uq_sla_priority_department",
            ),
        ]
        indexes = [
            models.Index(fields=["priority", "is_active"], name="idx_sla_prio_active"),
        ]

    def __str__(self):
        scope = self.department.code if self.department else "Global"
        return f"{self.name} ({self.priority} - {scope})"


class TicketSLA(models.Model):
    """Per-ticket SLA deadline snapshot and breach tracking."""

    ticket = models.OneToOneField(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="sla",
    )
    policy = models.ForeignKey(
        SLAPolicy,
        on_delete=models.PROTECT,
        related_name="ticket_slas",
    )
    response_due_at = models.DateTimeField(db_index=True)
    resolution_due_at = models.DateTimeField(db_index=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    response_breached = models.BooleanField(default=False, db_index=True)
    resolution_breached = models.BooleanField(default=False, db_index=True)
    warning_sent_at = models.DateTimeField(null=True, blank=True)
    breach_notified_at = models.DateTimeField(null=True, blank=True)

    paused_at = models.DateTimeField(null=True, blank=True)
    total_paused_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sla_ticketsla"
        indexes = [
            models.Index(fields=["resolution_due_at", "resolution_breached"], name="idx_tsla_res_breach"),
            models.Index(fields=["response_due_at", "response_breached"], name="idx_tsla_resp_breach"),
        ]

    def __str__(self):
        return f"SLA({self.ticket.ticket_number})"


class Escalation(models.Model):
    """Automated SLA breach or manual incident escalation record."""

    class EscalationType(models.TextChoices):
        RESPONSE_BREACH = "RESPONSE_BREACH", "Response SLA Breach"
        RESOLUTION_BREACH = "RESOLUTION_BREACH", "Resolution SLA Breach"
        MANUAL = "MANUAL", "Manual Escalation"

    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="escalations",
    )
    ticket_sla = models.ForeignKey(
        TicketSLA,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="escalations",
    )
    escalation_type = models.CharField(max_length=30, choices=EscalationType.choices)
    dedup_key = models.CharField(max_length=100, unique=True, null=True, blank=True)

    escalated_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escalations_initiated",
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escalations_received",
    )
    reason = models.TextField()
    is_acknowledged = models.BooleanField(default=False, db_index=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escalations_acknowledged",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sla_escalation"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"], name="idx_esc_ticket_created"),
        ]

    def __str__(self):
        return f"Escalation({self.ticket.ticket_number}, {self.escalation_type})"
