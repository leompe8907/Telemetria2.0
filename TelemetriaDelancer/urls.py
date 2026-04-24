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
from .ml.views import MLAnomaliesView, MLForecastView, MLSegmentsView, MLChurnRiskView
from .health_views import (
    HealthCheckView,
    DetailedHealthCheckView,
    MetricsView
)
from .auth_views import LoginView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    # Endpoints de telemetría
    path('telemetry/sync/', TelemetrySyncView.as_view(), name='telemetry-sync'),
    path('telemetry/merge/ott/', MergeOTTView.as_view(), name='telemetry-merge-ott'),
    path('telemetry/analytics/', AnalyticsView.as_view(), name='telemetry-analytics'),
    path('telemetry/period-analysis/', PeriodAnalysisView.as_view(), name='telemetry-period-analysis'),
    path('telemetry/ml/anomalies/', MLAnomaliesView.as_view(), name='telemetry-ml-anomalies'),
    path('telemetry/ml/forecast/', MLForecastView.as_view(), name='telemetry-ml-forecast'),
    path('telemetry/ml/segments/', MLSegmentsView.as_view(), name='telemetry-ml-segments'),
    path('telemetry/ml/churn/', MLChurnRiskView.as_view(), name='telemetry-ml-churn'),
    path('telemetry/users/analysis/general/', GeneralUsersAnalysisView.as_view(), name='users-analysis-general'),
    path('telemetry/users/analysis/', UserAnalysisView.as_view(), name='user-analysis'),
    path('telemetry/users/analysis/date-range/', UserDateRangeAnalysisView.as_view(), name='user-analysis-date-range'),
    
    # Endpoints de health check y monitoreo
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('health/detailed/', DetailedHealthCheckView.as_view(), name='health-check-detailed'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
]
