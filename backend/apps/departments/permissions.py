from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.models import User


class DepartmentPermission(BasePermission):
    """
    - ADMIN: full CRUD.
    - Other authenticated active users: read-only access.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role == User.Role.ADMIN
