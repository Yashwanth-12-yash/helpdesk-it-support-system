from django.urls import path

from .views import (
    AIClassifyTicketView,
    AISimilarTicketsView,
    AISuggestSolutionsView,
    AISummarizeTicketView,
)

urlpatterns = [
    path("ai/classify-ticket/", AIClassifyTicketView.as_view(), name="ai-classify-ticket"),
    path("ai/summarize-ticket/", AISummarizeTicketView.as_view(), name="ai-summarize-ticket"),
    path("ai/suggest-solutions/", AISuggestSolutionsView.as_view(), name="ai-suggest-solutions"),
    path("ai/similar-tickets/", AISimilarTicketsView.as_view(), name="ai-similar-tickets"),
]
