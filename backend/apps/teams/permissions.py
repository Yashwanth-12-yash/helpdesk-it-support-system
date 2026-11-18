from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.models import User


class SupportTeamPermission(BasePermission):
    """
    - ADMIN: full CRUD on teams and memberships.
    - MANAGER: read teams; manage memberships for teams in departments they manage.
    - ENGINEER / EMPLOYEE: read active teams.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False

        if request.method in SAFE_METHODS:
            return True

        if user.role == User.Role.ADMIN:
            return True

        if user.role == User.Role.MANAGER and getattr(view, "action", None) in {"members", "remove_member"}:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS or user.role == User.Role.ADMIN:
            return True

        if user.role == User.Role.MANAGER and getattr(view, "action", None) in {"members", "remove_member"}:
            return obj.department.manager_id == user.id

        return False
