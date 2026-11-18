from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrManager
from .selectors import get_dashboard_analytics, get_engineer_performance
from .services import export_tickets_csv_response


class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        data = get_dashboard_analytics(
            user=request.user,
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            department_id=request.query_params.get("department"),
        )
        return Response(data)


class EngineerPerformanceView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @extend_schema(responses={200: list})
    def get(self, request):
        data = get_engineer_performance(
            user=request.user,
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            department_id=request.query_params.get("department"),
        )
        return Response(data)


class ExportTicketsCSVView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        return export_tickets_csv_response(
            user=request.user,
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
            department_id=request.query_params.get("department"),
        )
