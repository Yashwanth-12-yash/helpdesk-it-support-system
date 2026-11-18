
from django.db.models import Count, Q, QuerySet

from apps.accounts.models import User
from .models import Department


def get_departments_queryset(*, requesting_user: User) -> QuerySet[Department]:
    qs = (
        Department.objects.select_related("manager")
        .annotate(team_count=Count("support_teams", distinct=True))
        .order_by("name")
    )

    if requesting_user.role == User.Role.ADMIN:
        return qs

    if requesting_user.role == User.Role.MANAGER:
        manager_scope = Q(manager=requesting_user)

        if requesting_user.department_id:
            manager_scope |= Q(pk=requesting_user.department_id)

        return qs.filter(is_active=True).filter(manager_scope).distinct()

    return qs.filter(is_active=True)
