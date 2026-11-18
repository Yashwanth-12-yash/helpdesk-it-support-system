from django.conf import settings
from django.db import models


class AIRecommendation(models.Model):
    """Persisted AI classification, summary, troubleshooting, and similar-ticket recommendations."""

    class RecommendationType(models.TextChoices):
        CLASSIFICATION = "CLASSIFICATION", "Classification"
        SUMMARY = "SUMMARY", "Incident Summary"
        TROUBLESHOOTING = "TROUBLESHOOTING", "Troubleshooting Suggestions"
        SIMILAR_TICKETS = "SIMILAR_TICKETS", "Similar Tickets"

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        APPLIED = "APPLIED", "Applied"
        DISMISSED = "DISMISSED", "Dismissed"

    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_recommendations",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_requests",
    )
    recommendation_type = models.CharField(max_length=30, choices=RecommendationType.choices)
    suggested_category = models.CharField(max_length=50, blank=True, default="")
    suggested_priority = models.CharField(max_length=20, blank=True, default="")
    suggested_department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_recommendations",
    )
    keywords = models.JSONField(default=list, blank=True)
    summary_text = models.TextField(blank=True, default="")
    troubleshooting_steps = models.JSONField(default=list, blank=True)
    related_article_ids = models.JSONField(default=list, blank=True)
    similar_ticket_ids = models.JSONField(default=list, blank=True)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    model_name = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_airecommendation"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticket", "recommendation_type", "created_at"], name="idx_ai_ticket_type"),
        ]

    def __str__(self):
        return f"AIRecommendation({self.recommendation_type}, {self.status})"
