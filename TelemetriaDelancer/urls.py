from django.urls import path
from .views import (
    TelemetrySyncView,
    MergeOTTView,
    AnalyticsView,
    PeriodAnalysisView
)

urlpatterns = [
    path('telemetry/sync/', TelemetrySyncView.as_view(), name='telemetry-sync'),
    path('telemetry/merge/ott/', MergeOTTView.as_view(), name='telemetry-merge-ott'),
    path('telemetry/analytics/', AnalyticsView.as_view(), name='telemetry-analytics'),
    path('telemetry/period-analysis/', PeriodAnalysisView.as_view(), name='telemetry-period-analysis'),
]
