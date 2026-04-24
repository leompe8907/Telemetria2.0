import logging
from datetime import datetime

from django.core.cache import cache
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from TelemetriaDelancer.mixins import CacheMixin
from TelemetriaDelancer.ml.constants import (
    ML_ANOMALIES_LATEST_CACHE_KEY,
    ML_FORECAST_LATEST_CACHE_KEY,
    ml_forecast_cache_key,
    ML_SEGMENTS_LATEST_CACHE_KEY,
    ml_segments_cache_key,
    ML_CHURN_LATEST_CACHE_KEY,
    ml_churn_cache_key,
)
from TelemetriaDelancer.ml.services import compute_churn_risk

logger = logging.getLogger(__name__)


def _parse_iso_date(value: str | None):
    """
    Parsea fechas YYYY-MM-DD a datetime (00:00) para reutilizar firmas existentes
    (que esperan datetime opcional).
    """
    if not value:
        return None
    return datetime.fromisoformat(value)


class MLAnomaliesView(CacheMixin, APIView):
    """
    Endpoint ML: detección de anomalías.

    Modos:
    - GET normal: calcula en demanda usando `get_anomaly_detection()` y cachea por request.
    - GET con `use_precomputed=1`: devuelve el último resultado guardado por Celery.

    Query params:
    - start_date: YYYY-MM-DD (opcional)
    - end_date: YYYY-MM-DD (opcional)
    - threshold_std: float (default 3.0)
    - use_precomputed: 0/1 (default 0)
    - no_cache: 0/1 (CacheMixin)
    """

    permission_classes = [AllowAny]
    cache_timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
    cache_key_prefix = "ml_anomalies"

    def get(self, request):
        use_precomputed = request.query_params.get("use_precomputed", "0") == "1"
        if use_precomputed:
            payload = cache.get(ML_ANOMALIES_LATEST_CACHE_KEY)
            if payload is None:
                return Response(
                    {
                        "success": False,
                        "error": "NO_PRECOMPUTED_RESULT",
                        "message": "No hay resultado precomputado en cache todavía.",
                        "hint": "Ejecuta la tarea Celery de anomalías o llama al endpoint sin use_precomputed.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(payload, status=status.HTTP_200_OK)

        return self.get_cached_response(request, self._compute)

    def _compute(self, request):
        threshold_std = float(request.query_params.get("threshold_std", 3.0))
        start_date = _parse_iso_date(request.query_params.get("start_date"))
        end_date = _parse_iso_date(request.query_params.get("end_date"))

        from TelemetriaDelancer.panaccess.analytics import get_anomaly_detection

        logger.info(
            "ML anomalies requested (threshold_std=%s, start_date=%s, end_date=%s)",
            threshold_std,
            start_date.date().isoformat() if start_date else None,
            end_date.date().isoformat() if end_date else None,
        )

        anomalies = get_anomaly_detection(
            threshold_std=threshold_std,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "threshold_std": threshold_std,
                "start_date": start_date.date().isoformat() if start_date else None,
                "end_date": end_date.date().isoformat() if end_date else None,
            },
            "data": anomalies,
        }


class MLForecastView(CacheMixin, APIView):
    """
    Endpoint ML: forecasting (serie temporal) de demanda.

    Baseline: `get_time_series_analysis()` (requiere Pandas/NumPy según `analytics.py`).

    Modos:
    - GET normal: calcula en demanda y cachea por request (CacheMixin).
    - GET con `use_precomputed=1`: devuelve cache precomputado por Celery.

    Query params:
    - channel: str (opcional; None = todos)
    - forecast_days: int (default 7)
    - start_date: YYYY-MM-DD (opcional)
    - end_date: YYYY-MM-DD (opcional)
    - use_precomputed: 0/1 (default 0)
    - no_cache: 0/1 (CacheMixin)
    """

    permission_classes = [AllowAny]
    cache_timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
    cache_key_prefix = "ml_forecast"

    def get(self, request):
        # Por defecto servimos precomputado para no sobrecargar el servidor.
        use_precomputed = request.query_params.get("use_precomputed", "1") == "1"
        channel = request.query_params.get("channel")
        forecast_days = int(request.query_params.get("forecast_days", 7))

        if use_precomputed:
            key = ml_forecast_cache_key(channel=channel, forecast_days=forecast_days)
            payload = cache.get(key)
            if payload is None:
                # fallback a "latest" genérico (si existe)
                payload = cache.get(ML_FORECAST_LATEST_CACHE_KEY)
            if payload is None:
                return Response(
                    {
                        "success": False,
                        "error": "NO_PRECOMPUTED_RESULT",
                        "message": "No hay forecast precomputado en cache todavía.",
                        "hint": "Ejecuta la tarea Celery de forecast o llama al endpoint sin use_precomputed.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(payload, status=status.HTTP_200_OK)

        return self.get_cached_response(request, self._compute)

    def _compute(self, request):
        channel = request.query_params.get("channel")
        forecast_days = int(request.query_params.get("forecast_days", 7))
        start_date = _parse_iso_date(request.query_params.get("start_date"))
        end_date = _parse_iso_date(request.query_params.get("end_date"))

        from TelemetriaDelancer.panaccess.analytics import get_time_series_analysis

        try:
            forecast = get_time_series_analysis(
                channel=channel,
                start_date=start_date,
                end_date=end_date,
                forecast_days=forecast_days,
            )
        except ImportError as e:
            # analytics.py requiere Pandas/NumPy para esta función
            return {
                "success": False,
                "error": "PANDAS_REQUIRED",
                "message": str(e),
                "hint": "Instala dependencias con: pip install pandas numpy",
            }

        return {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "channel": channel,
                "forecast_days": forecast_days,
                "start_date": start_date.date().isoformat() if start_date else None,
                "end_date": end_date.date().isoformat() if end_date else None,
            },
            "data": forecast,
        }


class MLSegmentsView(CacheMixin, APIView):
    """
    Endpoint ML: segmentación de usuarios (K-means baseline).

    Modos:
    - GET normal: calcula en demanda y cachea por request.
    - GET con `use_precomputed=1`: devuelve cache precomputado por Celery.

    Query params:
    - n_segments: int (default 4)
    - window_days: int (default 30) -> ventana de datos usada (se aplica como filtro por dataDate)
    - use_precomputed: 0/1
    - no_cache: 0/1
    """

    permission_classes = [AllowAny]
    cache_timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
    cache_key_prefix = "ml_segments"

    def get(self, request):
        use_precomputed = request.query_params.get("use_precomputed", "0") == "1"
        n_segments = int(request.query_params.get("n_segments", 4))
        window_days = int(request.query_params.get("window_days", 30))

        if use_precomputed:
            key = ml_segments_cache_key(n_segments=n_segments, window_days=window_days)
            payload = cache.get(key) or cache.get(ML_SEGMENTS_LATEST_CACHE_KEY)
            if payload is None:
                return Response(
                    {
                        "success": False,
                        "error": "NO_PRECOMPUTED_RESULT",
                        "message": "No hay segmentación precomputada en cache todavía.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(payload, status=status.HTTP_200_OK)

        return self.get_cached_response(request, self._compute)

    def _compute(self, request):
        from datetime import timedelta

        n_segments = int(request.query_params.get("n_segments", 4))
        window_days = int(request.query_params.get("window_days", 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window_days)

        from TelemetriaDelancer.panaccess.analytics import get_user_segmentation_analysis

        try:
            segments = get_user_segmentation_analysis(
                start_date=start_date,
                end_date=end_date,
                n_segments=n_segments,
            )
        except ImportError as e:
            return {
                "success": False,
                "error": "PANDAS_REQUIRED",
                "message": str(e),
                "hint": "Instala dependencias con: pip install pandas numpy",
            }

        return {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "n_segments": n_segments,
                "window_days": window_days,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
            },
            "data": segments,
        }


class MLChurnRiskView(CacheMixin, APIView):
    """
    Endpoint ML: riesgo de churn (heurístico, sin dependencias extra).

    Modos:
    - GET normal: calcula en demanda y cachea por request.
    - GET con `use_precomputed=1`: devuelve cache precomputado por Celery.

    Query params:
    - window_days: int (default 14)
    - min_views: int (default 3)
    - use_precomputed: 0/1
    - no_cache: 0/1
    """

    permission_classes = [AllowAny]
    cache_timeout = getattr(settings, "CACHE_TIMEOUT_ANALYTICS", 1800)
    cache_key_prefix = "ml_churn"

    def get(self, request):
        use_precomputed = request.query_params.get("use_precomputed", "0") == "1"
        window_days = int(request.query_params.get("window_days", 14))

        if use_precomputed:
            key = ml_churn_cache_key(window_days=window_days)
            payload = cache.get(key) or cache.get(ML_CHURN_LATEST_CACHE_KEY)
            if payload is None:
                return Response(
                    {
                        "success": False,
                        "error": "NO_PRECOMPUTED_RESULT",
                        "message": "No hay churn precomputado en cache todavía.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(payload, status=status.HTTP_200_OK)

        return self.get_cached_response(request, self._compute)

    def _compute(self, request):
        window_days = int(request.query_params.get("window_days", 14))
        min_views = int(request.query_params.get("min_views", 3))

        data = compute_churn_risk(window_days=window_days, min_views=min_views)
        return {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "filters": {"window_days": window_days, "min_views": min_views},
            "data": data,
        }

