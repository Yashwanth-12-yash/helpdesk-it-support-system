from django.urls import path

from .views import (
    AttachmentDownloadView,
    TicketAttachmentListCreateView,
    TicketCommentListCreateView,
)

urlpatterns = [
    path("tickets/<int:ticket_id>/comments/", TicketCommentListCreateView.as_view(), name="ticket-comments"),
    path("tickets/<int:ticket_id>/attachments/", TicketAttachmentListCreateView.as_view(), name="ticket-attachments"),
    path("attachments/<int:pk>/download/", AttachmentDownloadView.as_view(), name="attachment-download"),
]
