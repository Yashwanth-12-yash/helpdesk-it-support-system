from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SupportTeamViewSet

router = DefaultRouter()
router.register(r"teams", SupportTeamViewSet, basename="team")

urlpatterns = [
    path("", include(router.urls)),
]
