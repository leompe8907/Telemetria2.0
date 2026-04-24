ML_ANOMALIES_LATEST_CACHE_KEY = "telemetria:ml:anomalies:latest"

# Forecast: keys por canal/horizonte para servir rápido al dashboard
ML_FORECAST_LATEST_CACHE_KEY = "telemetria:ml:forecast:latest"

def ml_forecast_cache_key(channel: str | None, forecast_days: int) -> str:
    ch = (channel or "ALL").strip() or "ALL"
    return f"telemetria:ml:forecast:{ch}:{int(forecast_days)}"


# Segmentación
ML_SEGMENTS_LATEST_CACHE_KEY = "telemetria:ml:segments:latest"

def ml_segments_cache_key(n_segments: int, window_days: int) -> str:
    return f"telemetria:ml:segments:{int(n_segments)}:{int(window_days)}"


# Churn / riesgo (heurístico)
ML_CHURN_LATEST_CACHE_KEY = "telemetria:ml:churn:latest"

def ml_churn_cache_key(window_days: int) -> str:
    return f"telemetria:ml:churn:{int(window_days)}"

