from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


class IsAdminUserRole(BasePermission):
    """Allows access strictly to active users with the ADMIN role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == User.Role.ADMIN
        )


class CanViewOrManageUsers(BasePermission):
    """
    - ADMIN: full read/write access to all user endpoints.
    - MANAGER: read-only access (GET, HEAD, OPTIONS) to look up engineers and employees.
    - ENGINEER / EMPLOYEE: denied.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False

        if user.role == User.Role.ADMIN:
            return True

        if user.role == User.Role.MANAGER and request.method in SAFE_METHODS:
            return True

        return False
