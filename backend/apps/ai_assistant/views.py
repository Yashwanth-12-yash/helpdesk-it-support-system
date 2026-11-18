from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.tickets.models import Ticket
from apps.tickets.permissions import user_can_view_ticket
from common.permissions import IsStaffSupportRole
from .serializers import ClassifyTicketInputSerializer, TicketIdInputSerializer
from .services import (
    classify_ticket_with_ai,
    find_similar_resolved_tickets,
    suggest_solutions_with_ai,
    summarize_ticket_with_ai,
)


def _get_authorized_ticket(user, ticket_id: int) -> Ticket:
    ticket = get_object_or_404(Ticket.objects.select_related("department", "support_team"), pk=ticket_id)
    if not user_can_view_ticket(user, ticket):
        raise PermissionDenied("You do not have permission to access this ticket.")
    return ticket


class AIClassifyTicketView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_assistant"

    @extend_schema(request=ClassifyTicketInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = ClassifyTicketInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = None
        title = serializer.validated_data.get("title", "")
        description = serializer.validated_data.get("description", "")

        if serializer.validated_data.get("ticket_id"):
            ticket = _get_authorized_ticket(request.user, serializer.validated_data["ticket_id"])
            title = ticket.title
            description = ticket.description

        result = classify_ticket_with_ai(
            user=request.user,
            title=title,
            description=description,
            ticket=ticket,
        )
        return Response(result)


class AISummarizeTicketView(APIView):
    permission_classes = [IsAuthenticated, IsStaffSupportRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_assistant"

    @extend_schema(request=TicketIdInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = TicketIdInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = _get_authorized_ticket(request.user, serializer.validated_data["ticket_id"])
        return Response(summarize_ticket_with_ai(user=request.user, ticket=ticket))


class AISuggestSolutionsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffSupportRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_assistant"

    @extend_schema(request=TicketIdInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = TicketIdInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = _get_authorized_ticket(request.user, serializer.validated_data["ticket_id"])
        return Response(suggest_solutions_with_ai(user=request.user, ticket=ticket))


class AISimilarTicketsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffSupportRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_assistant"

    @extend_schema(request=TicketIdInputSerializer, responses={200: dict})
    def post(self, request):
        serializer = TicketIdInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = _get_authorized_ticket(request.user, serializer.validated_data["ticket_id"])
        return Response(find_similar_resolved_tickets(user=request.user, ticket=ticket))
