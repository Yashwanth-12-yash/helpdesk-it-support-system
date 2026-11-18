from django.urls import path

from .views import DashboardAnalyticsView, EngineerPerformanceView, ExportTicketsCSVView

urlpatterns = [
    path("analytics/dashboard/", DashboardAnalyticsView.as_view(), name="analytics-dashboard"),
    path("analytics/performance/", EngineerPerformanceView.as_view(), name="analytics-performance"),
    path("analytics/export-csv/", ExportTicketsCSVView.as_view(), name="analytics-export-csv"),
]
