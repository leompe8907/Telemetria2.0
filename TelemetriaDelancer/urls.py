from django.urls import path
from .views import (
    TestTelemetryFetch,
    TestTelemetryFetchAll,
    TestTelemetryFetchNew,
    TestTelemetryFetchPage
)

urlpatterns = [
    # Endpoint principal de prueba (descarga inteligente)
    path('telemetry/test/', TestTelemetryFetch.as_view(), name='telemetry-test'),
    path('telemetry/test/smart/', TestTelemetryFetch.as_view(), name='telemetry-test-smart'),
    
    # Endpoint para descargar todos los registros
    path('telemetry/test/all/', TestTelemetryFetchAll.as_view(), name='telemetry-test-all'),
    
    # Endpoint para descargar solo registros nuevos
    path('telemetry/test/new/', TestTelemetryFetchNew.as_view(), name='telemetry-test-new'),
    
    # Endpoint para obtener una página específica
    path('telemetry/test/page/', TestTelemetryFetchPage.as_view(), name='telemetry-test-page'),
]
