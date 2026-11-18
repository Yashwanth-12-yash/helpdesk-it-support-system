from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.models import User


class KnowledgeArticlePermission(BasePermission):
    """
    - All authenticated users: read PUBLISHED articles and recommendations.
    - ENGINEER: create and edit drafts.
    - MANAGER / ADMIN: create, edit, publish, and archive articles.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False

        if request.method in SAFE_METHODS:
            return True

        action = getattr(view, "action", None)
        if action in {"publish", "archive"}:
            return user.role in {User.Role.ADMIN, User.Role.MANAGER}

        return user.role in {User.Role.ADMIN, User.Role.MANAGER, User.Role.ENGINEER}
