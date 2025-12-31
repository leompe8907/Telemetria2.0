from django.urls import path
from .views import TelemetrySyncView

urlpatterns = [
    path('telemetry/sync/', TelemetrySyncView.as_view(), name='telemetry-sync'),
]
