from django.conf import settings
from django.db import models


class SupportTeam(models.Model):
    """Specialized IT support queue belonging to a Department."""

    name = models.CharField(max_length=120, unique=True)
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        related_name="support_teams",
    )
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teams_supportteam"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["department", "is_active"], name="idx_team_dept_active"),
        ]

    def __str__(self):
        return f"{self.name} ({self.department.code})"


class TeamMembership(models.Model):
    """Maps Support Engineers and Managers to Support Teams."""

    team = models.ForeignKey(
        SupportTeam,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "teams_teammembership"
        ordering = ["-is_primary", "joined_at"]
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="uq_team_membership_team_user"),
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_teammember_user"),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.team.name}"
