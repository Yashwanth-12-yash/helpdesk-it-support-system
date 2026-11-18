
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tickets.models import Ticket
from apps.tickets.permissions import user_can_view_ticket

from .models import TicketAttachment, TicketComment
from .serializers import (
    TicketAttachmentSerializer,
    TicketAttachmentUploadSerializer,
    TicketCommentCreateSerializer,
    TicketCommentSerializer,
)
from .services import add_ticket_attachment, add_ticket_comment


def _get_authorized_ticket(user: User, ticket_id: int) -> Ticket:
    ticket = get_object_or_404(
        Ticket.objects.select_related("department", "support_team"),
        pk=ticket_id,
    )

    if not user_can_view_ticket(user, ticket):
        raise PermissionDenied(
            "You do not have permission to access this ticket."
        )

    return ticket


class TicketCommentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TicketCommentSerializer(many=True))
    def get(self, request, ticket_id: int):
        ticket = _get_authorized_ticket(request.user, ticket_id)

        qs = TicketComment.objects.filter(
            ticket=ticket
        ).select_related("author")

        if request.user.role == User.Role.EMPLOYEE:
            qs = qs.filter(is_internal=False)

        return Response(TicketCommentSerializer(qs, many=True).data)

    @extend_schema(
        request=TicketCommentCreateSerializer,
        responses=TicketCommentSerializer,
    )
    def post(self, request, ticket_id: int):
        ticket = _get_authorized_ticket(request.user, ticket_id)

        serializer = TicketCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = add_ticket_comment(
            ticket=ticket,
            author=request.user,
            body=serializer.validated_data["body"],
            is_internal=serializer.validated_data["is_internal"],
        )

        return Response(
            TicketCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )


class TicketAttachmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(responses=TicketAttachmentSerializer(many=True))
    def get(self, request, ticket_id: int):
        ticket = _get_authorized_ticket(request.user, ticket_id)

        qs = TicketAttachment.objects.filter(
            ticket=ticket
        ).select_related("uploaded_by")

        return Response(TicketAttachmentSerializer(qs, many=True).data)

    @extend_schema(
        request=TicketAttachmentUploadSerializer,
        responses=TicketAttachmentSerializer,
    )
    def post(self, request, ticket_id: int):
        ticket = _get_authorized_ticket(request.user, ticket_id)

        serializer = TicketAttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            attachment = add_ticket_attachment(
                ticket=ticket,
                uploaded_by=request.user,
                uploaded_file=serializer.validated_data["file"],
                comment=serializer.validated_data.get("comment"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(detail=exc.messages)

        return Response(
            TicketAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED,
        )


class AttachmentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        attachment = get_object_or_404(
            TicketAttachment.objects.select_related(
                "ticket",
                "ticket__department",
                "ticket__support_team",
            ),
            pk=pk,
        )

        if not user_can_view_ticket(request.user, attachment.ticket):
            raise PermissionDenied(
                "You do not have permission to download this attachment."
            )

        response = FileResponse(
            attachment.file.open("rb"),
            content_type=attachment.content_type or "application/octet-stream",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{attachment.original_filename}"'
        )

        return response
