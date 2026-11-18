from django.conf import settings
from django.db import models

from apps.tickets.models import Ticket


class KnowledgeArticle(models.Model):
    """Internal IT troubleshooting and solution repository."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.CharField(
        max_length=30,
        choices=Ticket.Category.choices,
        default=Ticket.Category.OTHER,
        db_index=True,
    )
    summary = models.TextField(blank=True, default="")
    content = models.TextField()
    troubleshooting_steps = models.TextField(blank=True, default="")
    keywords = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_articles",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_articles",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge_base_knowledgearticle"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "category"], name="idx_kb_status_cat"),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"
