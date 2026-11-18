
from django.db.models import Count, Q
from django.utils import timezone

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.audit.services import record_audit_event
from common.permissions import IsAdmin, IsAdminOrManager
from .models import Escalation, SLAPolicy, TicketSLA
from .serializers import EscalationSerializer, SLAPolicySerializer
from .services import acknowledge_escalation


def get_manager_department_scope(user):
    """
    Return records belonging to departments managed by this Manager
    or the Manager's assigned department.
    """
    scope = Q(department__manager=user)

    if user.department_id:
        scope |= Q(department_id=user.department_id)

    return scope


def get_manager_ticket_department_scope(user):
    """
    Return ticket records belonging to departments managed by this
    Manager or the Manager's assigned department.
    """
    scope = Q(ticket__department__manager=user)

    if user.department_id:
        scope |= Q(ticket__department_id=user.department_id)

    return scope


class SLAPolicyViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = SLAPolicySerializer
    filterset_fields = ["priority", "department", "is_active"]

    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), IsAdminOrManager()]

        return [IsAuthenticated(), IsAdmin()]

    def get_queryset(self):
        qs = SLAPolicy.objects.select_related("department")

        if self.request.user.role == User.Role.ADMIN:
            return qs

        if self.request.user.role == User.Role.MANAGER:
            return qs.filter(
                Q(department__isnull=True)
                | get_manager_department_scope(self.request.user)
            )

        return SLAPolicy.objects.none()

    def perform_create(self, serializer):
        policy = serializer.save()

        record_audit_event(
            action="SLA_POLICY_CREATED",
            resource_type="SLAPolicy",
            resource_id=policy.id,
            actor=self.request.user,
            request=self.request,
            metadata={
                "name": policy.name,
                "priority": policy.priority,
            },
        )

    def perform_update(self, serializer):
        policy = serializer.save()

        record_audit_event(
            action="SLA_POLICY_UPDATED",
            resource_type="SLAPolicy",
            resource_id=policy.id,
            actor=self.request.user,
            request=self.request,
            metadata={
                "name": policy.name,
                "priority": policy.priority,
            },
        )


class SLAOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @extend_schema(responses={200: dict})
    def get(self, request):
        now = timezone.now()

        qs = TicketSLA.objects.select_related(
            "ticket",
            "ticket__department",
        )

        if request.user.role == User.Role.MANAGER:
            manager_scope = get_manager_ticket_department_scope(
                request.user
            )
            qs = qs.filter(manager_scope)

        stats = qs.aggregate(
            total_tracked=Count("id"),
            response_breach_count=Count(
                "id",
                filter=Q(response_breached=True),
            ),
            resolution_breach_count=Count(
                "id",
                filter=Q(resolution_breached=True),
            ),
            active_overdue=Count(
                "id",
                filter=Q(
                    resolved_at__isnull=True,
                    resolution_due_at__lt=now,
                ),
            ),
            resolved_within_sla=Count(
                "id",
                filter=Q(
                    resolved_at__isnull=False,
                    resolution_breached=False,
                ),
            ),
            total_resolved=Count(
                "id",
                filter=Q(resolved_at__isnull=False),
            ),
        )

        total_resolved = stats["total_resolved"] or 0

        compliance_rate = (
            round(
                (stats["resolved_within_sla"] / total_resolved) * 100,
                2,
            )
            if total_resolved
            else None
        )

        escalations = Escalation.objects.filter(
            is_acknowledged=False
        )

        if request.user.role == User.Role.MANAGER:
            escalations = escalations.filter(
                get_manager_ticket_department_scope(request.user)
            )

        return Response(
            {
                "total_tracked": stats["total_tracked"],
                "response_breached": stats["response_breach_count"],
                "resolution_breached": stats["resolution_breach_count"],
                "active_overdue": stats["active_overdue"],
                "resolved_within_sla": stats["resolved_within_sla"],
                "total_resolved": stats["total_resolved"],
                "sla_compliance_percentage": compliance_rate,
                "unacknowledged_escalations": escalations.count(),
            }
        )


class EscalationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EscalationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    filterset_fields = [
        "escalation_type",
        "is_acknowledged",
        "ticket",
    ]

    def get_queryset(self):
        qs = Escalation.objects.select_related(
            "ticket",
            "ticket__department",
            "escalated_from",
            "escalated_to",
            "acknowledged_by",
        )

        if self.request.user.role == User.Role.MANAGER:
            qs = qs.filter(
                get_manager_ticket_department_scope(self.request.user)
            )

        return qs

    @extend_schema(request=None, responses=EscalationSerializer)
    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        escalation = self.get_object()

        updated = acknowledge_escalation(
            escalation=escalation,
            actor=request.user,
        )

        return Response(
            EscalationSerializer(updated).data,
            status=status.HTTP_200_OK,
        )
