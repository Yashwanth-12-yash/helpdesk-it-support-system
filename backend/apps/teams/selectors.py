
from django.db.models import Prefetch, Q, QuerySet

from apps.accounts.models import User
from .models import SupportTeam, TeamMembership


def get_teams_queryset(*, requesting_user: User) -> QuerySet[SupportTeam]:
    membership_qs = (
        TeamMembership.objects.select_related("user")
        .order_by("-is_primary", "user__first_name")
    )

    qs = (
        SupportTeam.objects.select_related("department", "lead")
        .prefetch_related(Prefetch("memberships", queryset=membership_qs))
        .order_by("name")
    )

    # Admin: access all teams
    if requesting_user.role == User.Role.ADMIN:
        return qs

    # Manager: access only their department's teams
    if requesting_user.role == User.Role.MANAGER:
        manager_scope = Q(department__manager=requesting_user)

        if requesting_user.department_id:
            manager_scope |= Q(department_id=requesting_user.department_id)

        return qs.filter(is_active=True).filter(manager_scope).distinct()

    # Engineer: access only teams in their own department
    if requesting_user.role == User.Role.ENGINEER:
        if not requesting_user.department_id:
            return qs.none()

        return qs.filter(
            is_active=True,
            department_id=requesting_user.department_id,
        )

    # Employee: retain existing active-team visibility
    return qs.filter(is_active=True)
