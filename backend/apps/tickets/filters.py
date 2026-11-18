import django_filters
from django.utils import timezone

from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Ticket.Status.choices)
    priority = django_filters.MultipleChoiceFilter(choices=Ticket.Priority.choices)
    category = django_filters.MultipleChoiceFilter(choices=Ticket.Category.choices)
    department = django_filters.NumberFilter(field_name="department_id")
    support_team = django_filters.NumberFilter(field_name="support_team_id")
    assigned_engineer = django_filters.NumberFilter(field_name="assigned_engineer_id")
    created_by = django_filters.NumberFilter(field_name="created_by_id")
    my_tickets = django_filters.BooleanFilter(method="filter_my_tickets")
    assigned_to_me = django_filters.BooleanFilter(method="filter_assigned_to_me")
    overdue = django_filters.BooleanFilter(method="filter_overdue")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Ticket
        fields = [
            "status",
            "priority",
            "category",
            "department",
            "support_team",
            "assigned_engineer",
            "created_by",
        ]

    def filter_my_tickets(self, queryset, name, value):
        if value and getattr(self.request, "user", None):
            return queryset.filter(created_by=self.request.user)
        return queryset

    def filter_assigned_to_me(self, queryset, name, value):
        if value and getattr(self.request, "user", None):
            return queryset.filter(assigned_engineer=self.request.user)
        return queryset

    def filter_overdue(self, queryset, name, value):
        now = timezone.now()
        active_statuses = [
            Ticket.Status.OPEN,
            Ticket.Status.ASSIGNED,
            Ticket.Status.IN_PROGRESS,
            Ticket.Status.ON_HOLD,
            Ticket.Status.REOPENED,
        ]
        if value is True:
            return queryset.filter(status__in=active_statuses, resolution_deadline__lt=now)
        if value is False:
            return queryset.exclude(status__in=active_statuses, resolution_deadline__lt=now)
        return queryset
