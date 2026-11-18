import logging
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("apps.health")


class HealthCheckView(APIView):
    """Verifies MySQL database and Redis cache connectivity."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="System Health Check",
        description="Checks connectivity to MySQL 8 database and Redis cache.",
        responses={200: dict, 503: dict},
    )
    def get(self, request):
        db_ok = True
        redis_ok = True

        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError as exc:
            logger.error("MySQL health check failed: %s", exc)
            db_ok = False

        try:
            cache.set("healthcheck_ping", "pong", timeout=10)
            redis_ok = cache.get("healthcheck_ping") == "pong"
        except Exception as exc:
            logger.error("Redis health check failed: %s", exc)
            redis_ok = False

        is_healthy = db_ok and redis_ok
        http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(
            {
                "status": "healthy" if is_healthy else "degraded",
                "services": {
                    "mysql": "up" if db_ok else "down",
                    "redis": "up" if redis_ok else "down",
                },
            },
            status=http_status,
        )
