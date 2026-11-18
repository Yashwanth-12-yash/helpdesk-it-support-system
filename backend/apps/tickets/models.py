from django.conf import settings
from django.db import models


class TicketSequence(models.Model):
    """Per-year atomic counter for generating HD-YYYY-NNNNN ticket numbers."""

    year = models.PositiveIntegerField(primary_key=True)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "tickets_ticketsequence"


class Ticket(models.Model):
    """Primary IT Support Ticket entity."""

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        ON_HOLD = "ON_HOLD", "On Hold"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    class Category(models.TextChoices):
        HARDWARE = "HARDWARE", "Hardware"
        SOFTWARE = "SOFTWARE", "Software"
        NETWORK = "NETWORK", "Network & VPN"
        ACCESS = "ACCESS", "Access & Identity"
        EMAIL = "EMAIL", "Email & Collaboration"
        SECURITY = "SECURITY", "Security Incident"
        OTHER = "OTHER", "Other"

    ticket_number = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_tickets",
    )
    assigned_engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        related_name="tickets",
    )
    support_team = models.ForeignKey(
        "teams.SupportTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    response_deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    resolution_deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    first_responded_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default="")
    reopen_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tickets_ticket"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"], name="idx_ticket_status_prio"),
            models.Index(fields=["department", "status"], name="idx_ticket_dept_status"),
            models.Index(fields=["assigned_engineer", "status"], name="idx_ticket_eng_status"),
            models.Index(fields=["created_by", "created_at"], name="idx_ticket_creator_created"),
        ]

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"


class TicketHistory(models.Model):
    """Immutable chronological history of ticket field, status, and assignment mutations."""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_changes",
    )
    action_type = models.CharField(max_length=50)
    field_name = models.CharField(max_length=64, blank=True, default="")
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tickets_tickethistory"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"], name="idx_tickethist_ticket_created"),
        ]

    def __str__(self):
        return f"{self.ticket.ticket_number}: {self.action_type}"
