from django.conf import settings
from django.db import models


class Department(models.Model):
    """Organizational department (e.g., IT Infrastructure, Security, Finance)."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, default="")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "departments_department"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["manager", "is_active"], name="idx_dept_mgr_active"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
