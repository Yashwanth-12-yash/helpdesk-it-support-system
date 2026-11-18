from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import SupportTeamPermission
from .selectors import get_teams_queryset
from .serializers import (
    SupportTeamSerializer,
    SupportTeamWriteSerializer,
    TeamMembershipSerializer,
    TeamMembershipWriteSerializer,
)
from .services import (
    add_team_member,
    create_support_team,
    remove_team_member,
    update_support_team,
)


class SupportTeamViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticated, SupportTeamPermission]
    filterset_fields = ["department", "is_active", "lead"]
    search_fields = ["name", "description", "department__name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return get_teams_queryset(requesting_user=self.request.user)

    def get_serializer_class(self):
        if self.action in {"create", "partial_update", "update"}:
            return SupportTeamWriteSerializer
        if self.action == "members" and self.request.method == "POST":
            return TeamMembershipWriteSerializer
        return SupportTeamSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = create_support_team(created_by=request.user, **serializer.validated_data)
        return Response(SupportTeamSerializer(team).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        team = self.get_object()
        serializer = self.get_serializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = update_support_team(team=team, updated_by=request.user, **serializer.validated_data)
        return Response(SupportTeamSerializer(updated).data)

    @extend_schema(responses={200: TeamMembershipSerializer(many=True), 201: TeamMembershipSerializer})
    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        team = self.get_object()
        if request.method == "GET":
            return Response(TeamMembershipSerializer(team.memberships.all(), many=True).data)

        serializer = TeamMembershipWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = add_team_member(
            team=team,
            user=serializer.validated_data["user"],
            is_primary=serializer.validated_data["is_primary"],
            actor=request.user,
        )
        return Response(TeamMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={204: None})
    @action(detail=True, methods=["delete"], url_path=r"members/(?P<user_id>\d+)")
    def remove_member(self, request, pk=None, user_id=None):
        team = self.get_object()
        remove_team_member(team=team, user_id=int(user_id), actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
