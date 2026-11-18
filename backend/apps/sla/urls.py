from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EscalationViewSet, SLAOverviewView, SLAPolicyViewSet

router = DefaultRouter()
router.register(r"sla/policies", SLAPolicyViewSet, basename="sla-policy")
router.register(r"sla/escalations", EscalationViewSet, basename="sla-escalation")

urlpatterns = [
    path("sla/overview/", SLAOverviewView.as_view(), name="sla-overview"),
    path("", include(router.urls)),
]
