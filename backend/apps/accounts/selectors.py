
from django.db.models import Q, QuerySet

from .models import User


def get_users_queryset(*, requesting_user: User) -> QuerySet[User]:
    """
    Return users according to the requesting user's role.

    ADMIN:
        Can view all users.

    MANAGER:
        Can view active users belonging to departments they manage,
        including users in their own assigned department.

    ENGINEER / EMPLOYEE:
        No access is granted by the user-management permission class.
    """
    qs = (
        User.objects.select_related("department")
        .all()
        .order_by("-created_at")
    )

    if requesting_user.role == User.Role.ADMIN:
        return qs

    if requesting_user.role == User.Role.MANAGER:
        manager_scope = Q(department__manager=requesting_user)

        if requesting_user.department_id:
            manager_scope |= Q(department_id=requesting_user.department_id)

        return qs.filter(is_active=True).filter(manager_scope).distinct()

    return qs.none()


def get_user_by_id(user_id: int) -> User:
    return User.objects.get(pk=user_id)
