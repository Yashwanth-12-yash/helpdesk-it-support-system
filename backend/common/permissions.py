from rest_framework.permissions import BasePermission


class RoleBasedPermission(BasePermission):
    """
    Base permission checking `allowed_roles` defined on a View/ViewSet.
    Usage:
        permission_classes = [IsAuthenticated, RoleBasedPermission]
        allowed_roles = {"ADMIN", "MANAGER"}
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False

        allowed_roles = getattr(view, "allowed_roles", None)
        if allowed_roles is None:
            return True

        return getattr(request.user, "role", None) in allowed_roles


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == "ADMIN"
        )


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) in {"ADMIN", "MANAGER"}
        )


class IsStaffSupportRole(BasePermission):
    """Allows ADMIN, MANAGER, and ENGINEER roles."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) in {"ADMIN", "MANAGER", "ENGINEER"}
        )
