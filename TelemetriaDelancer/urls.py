from django.urls import path
from .views import (
    TelemetrySyncView,
    MergeOTTView,
    AnalyticsView,
    PeriodAnalysisView,
    GeneralUsersAnalysisView,
    UserAnalysisView,
    UserDateRangeAnalysisView
)
from .health_views import (
    HealthCheckView,
    DetailedHealthCheckView,
    MetricsView
)

urlpatterns = [
    # Endpoints de telemetría
    path('telemetry/sync/', TelemetrySyncView.as_view(), name='telemetry-sync'),
    path('telemetry/merge/ott/', MergeOTTView.as_view(), name='telemetry-merge-ott'),
    path('telemetry/analytics/', AnalyticsView.as_view(), name='telemetry-analytics'),
    path('telemetry/period-analysis/', PeriodAnalysisView.as_view(), name='telemetry-period-analysis'),
    path('telemetry/users/analysis/general/', GeneralUsersAnalysisView.as_view(), name='users-analysis-general'),
    path('telemetry/users/analysis/', UserAnalysisView.as_view(), name='user-analysis'),
    path('telemetry/users/analysis/date-range/', UserDateRangeAnalysisView.as_view(), name='user-analysis-date-range'),
    
    # Endpoints de health check y monitoreo
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('health/detailed/', DetailedHealthCheckView.as_view(), name='health-check-detailed'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
]
