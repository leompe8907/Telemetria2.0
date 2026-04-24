from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.db.models import Count

from TelemetriaDelancer.models import MergedTelemetricOTTDelancer


@dataclass(frozen=True)
class ForecastModelMeta:
    channel: str
    trained_at: str
    window_days: int
    horizon_days: int
    features: list[str]


def _models_dir() -> Path:
    base = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    d = base / "ml_models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def model_path_for_channel(channel: str) -> Path:
    safe = "".join([c if c.isalnum() or c in (" ", "-", "_") else "_" for c in channel]).strip()
    safe = safe.replace(" ", "_")[:80] or "UNKNOWN"
    return _models_dir() / f"forecast_ridge_{safe}.joblib"


def meta_path_for_channel(channel: str) -> Path:
    return model_path_for_channel(channel).with_suffix(".meta.json")


def _date_range(start: date, end: date) -> list[date]:
    out = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur = cur + timedelta(days=1)
    return out


def fetch_daily_views(channel: str, start: date, end: date) -> list[tuple[date, int]]:
    """
    Devuelve views diarios (conteo de filas) para `channel`, rellenando días faltantes con 0.
    """
    qs = (
        MergedTelemetricOTTDelancer.objects.filter(
            dataName=channel,
            dataDate__isnull=False,
            dataDate__gte=start,
            dataDate__lte=end,
        )
        .values("dataDate")
        .annotate(views=Count("id"))
        .order_by("dataDate")
    )
    by_day = {row["dataDate"]: int(row["views"] or 0) for row in qs}
    return [(d, by_day.get(d, 0)) for d in _date_range(start, end)]


def build_features(series: list[tuple[date, int]]):
    """
    Serie diaria -> (X, y, feature_names, dates)
    Features:
      - lag_1, lag_7, lag_14
      - roll_mean_7, roll_mean_14
      - dow_0..dow_6 (one-hot)
      - is_weekend
    """
    vals = [v for _, v in series]
    days = [d for d, _ in series]

    def lag(i: int, k: int) -> int:
        j = i - k
        return vals[j] if j >= 0 else 0

    def roll_mean(i: int, w: int) -> float:
        if i <= 0:
            return 0.0
        start = max(0, i - w)
        window = vals[start:i]
        return float(sum(window) / max(len(window), 1))

    feature_names = [
        "lag_1",
        "lag_7",
        "lag_14",
        "roll_mean_7",
        "roll_mean_14",
        "is_weekend",
        *[f"dow_{i}" for i in range(7)],
    ]

    X = []
    y = []
    used_dates = []
    for i in range(len(series)):
        # Need at least 14 days of history for full feature set
        if i < 14:
            continue
        d = days[i]
        dow = d.weekday()
        row = [
            float(lag(i, 1)),
            float(lag(i, 7)),
            float(lag(i, 14)),
            float(roll_mean(i, 7)),
            float(roll_mean(i, 14)),
            1.0 if dow >= 5 else 0.0,
        ]
        row += [1.0 if dow == j else 0.0 for j in range(7)]

        X.append(row)
        y.append(float(vals[i]))
        used_dates.append(d)

    return X, y, feature_names, used_dates


def train_ridge(channel: str, window_days: int = 180, alpha: float = 1.0):
    """
    Entrena un RidgeRegression por canal sobre la serie diaria de views.
    Persiste artefacto (joblib) + metadata (json).
    """
    from sklearn.linear_model import Ridge
    import joblib

    today = date.today()
    start = today - timedelta(days=window_days - 1)

    series = fetch_daily_views(channel=channel, start=start, end=today)
    X, y, feature_names, used_dates = build_features(series)

    if len(y) < 30:
        raise ValueError(f"Datos insuficientes para entrenar {channel}: {len(y)} samples")

    model = Ridge(alpha=float(alpha), random_state=42)
    model.fit(X, y)

    model_path = model_path_for_channel(channel)
    meta_path = meta_path_for_channel(channel)

    joblib.dump(model, model_path)
    meta = ForecastModelMeta(
        channel=channel,
        trained_at=datetime.now().isoformat(),
        window_days=int(window_days),
        horizon_days=7,
        features=feature_names,
    )
    meta_path.write_text(json.dumps(meta.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "channel": channel,
        "model_path": str(model_path),
        "meta_path": str(meta_path),
        "trained_at": meta.trained_at,
        "samples": len(y),
    }


def load_model(channel: str):
    import joblib

    p = model_path_for_channel(channel)
    if not p.exists():
        return None
    return joblib.load(p)


def predict_next_days(channel: str, horizon_days: int = 7, window_days: int = 180):
    """
    Predice `horizon_days` hacia adelante usando autorregresión (se alimenta con sus propias predicciones).
    """
    model = load_model(channel)
    if model is None:
        raise FileNotFoundError(f"No hay modelo entrenado para channel={channel}")

    today = date.today()
    start = today - timedelta(days=window_days - 1)
    series = fetch_daily_views(channel=channel, start=start, end=today)

    # convert to mutable list for iterative forecasting
    series_days = [d for d, _ in series]
    series_vals = [float(v) for _, v in series]

    out = []
    for step in range(1, horizon_days + 1):
        d = today + timedelta(days=step)
        series_days.append(d)
        series_vals.append(0.0)  # placeholder

        # build feature row at last index using current vals
        i = len(series_vals) - 1
        dow = d.weekday()

        def lag(k: int) -> float:
            j = i - k
            return float(series_vals[j]) if j >= 0 else 0.0

        def roll_mean(w: int) -> float:
            start_i = max(0, i - w)
            window = series_vals[start_i:i]
            return float(sum(window) / max(len(window), 1))

        x = [
            lag(1),
            lag(7),
            lag(14),
            roll_mean(7),
            roll_mean(14),
            1.0 if dow >= 5 else 0.0,
            *[1.0 if dow == j else 0.0 for j in range(7)],
        ]

        y_hat = float(model.predict([x])[0])
        if y_hat < 0:
            y_hat = 0.0

        series_vals[i] = y_hat
        out.append({"dataDate": datetime(d.year, d.month, d.day).isoformat(), "forecast": y_hat})

    return out

