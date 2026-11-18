from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.sla.serializers import EscalationSerializer, ManualEscalationSerializer
from apps.sla.services import create_manual_escalation
from .filters import TicketFilter
from .permissions import TicketAccessPermission
from .selectors import get_ticket_history_queryset, get_tickets_queryset
from .serializers import (
    TicketAssignSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketHistorySerializer,
    TicketListSerializer,
    TicketReopenSerializer,
    TicketResolveSerializer,
    TicketStatusChangeSerializer,
    TicketUpdateSerializer,
)
from .services import (
    assign_ticket,
    change_ticket_status,
    create_ticket,
    reopen_ticket,
    resolve_ticket,
    update_ticket,
)


class TicketViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_classes = [IsAuthenticated, TicketAccessPermission]
    filterset_class = TicketFilter
    search_fields = ["ticket_number", "title", "description"]
    ordering_fields = ["created_at", "updated_at", "priority", "status", "resolution_deadline"]

    def get_queryset(self):
        qs = get_tickets_queryset(requesting_user=self.request.user)
        if self.action == "retrieve":
            qs = qs.select_related("sla", "sla__policy")
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "create":
            return TicketCreateSerializer
        if self.action in {"partial_update", "update"}:
            return TicketUpdateSerializer
        if self.action == "assign":
            return TicketAssignSerializer
        if self.action == "change_status":
            return TicketStatusChangeSerializer
        if self.action == "resolve":
            return TicketResolveSerializer
        if self.action == "reopen":
            return TicketReopenSerializer
        if self.action == "escalate":
            return ManualEscalationSerializer
        return TicketDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = create_ticket(created_by=request.user, request=request, **serializer.validated_data)
        return Response(TicketDetailSerializer(ticket).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        serializer = self.get_serializer(ticket, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = update_ticket(ticket=ticket, updated_by=request.user, request=request, **serializer.validated_data)
        return Response(TicketDetailSerializer(updated).data)

    @extend_schema(request=TicketAssignSerializer, responses=TicketDetailSerializer)
    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = assign_ticket(
            ticket=ticket,
            actor=request.user,
            request=request,
            **serializer.validated_data,
        )
        return Response(TicketDetailSerializer(updated).data)

    @extend_schema(request=TicketStatusChangeSerializer, responses=TicketDetailSerializer)
    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketStatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = change_ticket_status(
            ticket=ticket,
            new_status=serializer.validated_data["status"],
            note=serializer.validated_data["note"],
            actor=request.user,
            request=request,
        )
        return Response(TicketDetailSerializer(updated).data)

    @extend_schema(request=TicketResolveSerializer, responses=TicketDetailSerializer)
    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = resolve_ticket(
            ticket=ticket,
            actor=request.user,
            resolution_notes=serializer.validated_data["resolution_notes"],
            request=request,
        )
        return Response(TicketDetailSerializer(updated).data)

    @extend_schema(request=TicketReopenSerializer, responses=TicketDetailSerializer)
    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketReopenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = reopen_ticket(
            ticket=ticket,
            actor=request.user,
            reason=serializer.validated_data["reason"],
            request=request,
        )
        return Response(TicketDetailSerializer(updated).data)

    @extend_schema(responses=TicketHistorySerializer(many=True))
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        ticket = self.get_object()
        history_qs = get_ticket_history_queryset(ticket=ticket)
        return Response(TicketHistorySerializer(history_qs, many=True).data)

    @extend_schema(request=ManualEscalationSerializer, responses=EscalationSerializer)
    @action(detail=True, methods=["post"], url_path="escalate")
    def escalate(self, request, pk=None):
        ticket = self.get_object()
        serializer = ManualEscalationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_id = serializer.validated_data.get("escalated_to")
        target_user = User.objects.filter(pk=target_id, is_active=True).first() if target_id else None
        escalation = create_manual_escalation(
            ticket=ticket,
            escalated_by=request.user,
            reason=serializer.validated_data["reason"],
            escalated_to=target_user,
            request=request,
        )
        return Response(EscalationSerializer(escalation).data, status=status.HTTP_201_CREATED)
