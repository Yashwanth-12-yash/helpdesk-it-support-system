from django.conf import settings
from django.db import models

from common.utilities import generate_attachment_upload_path, validate_uploaded_file


class TicketComment(models.Model):
    """Chronological discussion comment or internal staff note on a ticket."""

    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ticket_comments",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments_ticketcomment"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"], name="idx_comment_ticket_created"),
            models.Index(fields=["ticket", "is_internal"], name="idx_comment_ticket_internal"),
        ]

    def __str__(self):
        return f"Comment({self.ticket.ticket_number}, by={self.author.email})"


class TicketAttachment(models.Model):
    """Supporting file attachment stored safely outside public web execution."""

    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    comment = models.ForeignKey(
        TicketComment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attachments",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_attachments",
    )
    file = models.FileField(
        upload_to=generate_attachment_upload_path,
        validators=[validate_uploaded_file],
        max_length=500,
    )
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True, default="application/octet-stream")
    file_size = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comments_ticketattachment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"], name="idx_attach_ticket_created"),
        ]

    def __str__(self):
        return f"Attachment({self.original_filename})"
