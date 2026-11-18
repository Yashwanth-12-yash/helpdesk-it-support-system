
from django.db.models import Q
from rest_framework.permissions import BasePermission

from apps.accounts.models import User


def user_can_view_ticket(user: User, ticket) -> bool:
    """Determine whether a user can view an individual ticket."""
    if not user or not user.is_authenticated or not user.is_active:
        return False

    if user.role == User.Role.ADMIN:
        return True

    if user.role == User.Role.MANAGER:
        return (
            ticket.department.manager_id == user.id
            or ticket.department_id == user.department_id
        )

    if user.role == User.Role.ENGINEER:
        if ticket.assigned_engineer_id == user.id:
            return True

        if ticket.support_team_id:
            return ticket.support_team.memberships.filter(
                user_id=user.id
            ).exists()

        return False

    # Employees can view only tickets they created.
    return ticket.created_by_id == user.id


class TicketAccessPermission(BasePermission):
    """Object-level role-based access control for tickets."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user_can_view_ticket(user, obj):
            return False

        action = getattr(view, "action", None)

        # All users with visibility can read the ticket.
        if request.method in {"GET", "HEAD", "OPTIONS"} or action == "history":
            return True

        # Assignment permissions.
        if action == "assign":
            return user.role in {
                User.Role.ADMIN,
                User.Role.MANAGER,
                User.Role.ENGINEER,
            }

        # Status changes and resolution.
        if action in {"change_status", "resolve"}:
            if user.role == User.Role.ADMIN:
                return True

            if user.role == User.Role.MANAGER:
                return (
                    obj.department.manager_id == user.id
                    or obj.department_id == user.department_id
                )

            if user.role == User.Role.ENGINEER:
                return obj.assigned_engineer_id == user.id

            return False

        # Reopening tickets.
        if action == "reopen":
            if user.role == User.Role.ADMIN:
                return True

            if user.role == User.Role.MANAGER:
                return (
                    obj.department.manager_id == user.id
                    or obj.department_id == user.department_id
                )

            return (
                user.role == User.Role.EMPLOYEE
                and obj.created_by_id == user.id
            )

        # PATCH / update permissions.
        if user.role == User.Role.ADMIN:
            return True

        if user.role == User.Role.MANAGER:
            return (
                obj.department.manager_id == user.id
                or obj.department_id == user.department_id
            )

        if user.role == User.Role.ENGINEER:
            return obj.assigned_engineer_id == user.id

        if user.role == User.Role.EMPLOYEE:
            return obj.created_by_id == user.id

        return False


def scope_tickets_queryset_for_user(qs, user: User):
    """Apply role-based row-level visibility to ticket querysets."""

    if user.role == User.Role.ADMIN:
        return qs

    if user.role == User.Role.MANAGER:
        return qs.filter(
            Q(department__manager=user)
            | Q(department_id=user.department_id)
        ).distinct()

    if user.role == User.Role.ENGINEER:
        return qs.filter(
            Q(assigned_engineer=user)
            | Q(support_team__memberships__user=user)
        ).distinct()

    # Employees see only tickets they created.
    return qs.filter(created_by=user)
