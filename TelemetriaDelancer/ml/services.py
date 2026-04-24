from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Count, Max, Q

from TelemetriaDelancer.models import MergedTelemetricOTTDelancer


def compute_churn_risk(window_days: int = 14, min_views: int = 3):
    """
    Heurística simple de riesgo de churn basada en telemetría OTT:

    - Se divide la ventana en 2 mitades: [prev] y [last]
    - Se calcula views por usuario en cada mitad
    - Riesgo:
      - high: 0 views en last_window y >= min_views en prev_window
      - medium: caída >= 50% (last <= prev/2) y prev >= min_views
      - low: resto

    Retorna un dict listo para API: resumen + top usuarios en riesgo.
    """
    window_days = int(window_days)
    if window_days < 2:
        window_days = 2

    half = window_days // 2
    today = date.today()
    start = today - timedelta(days=window_days - 1)
    split = today - timedelta(days=half - 1)

    qs = (
        MergedTelemetricOTTDelancer.objects.filter(
            subscriberCode__isnull=False,
            dataDate__isnull=False,
            dataDate__gte=start,
            dataDate__lte=today,
        )
        .values("subscriberCode")
        .annotate(
            last_seen=Max("dataDate"),
            views_last=Count("id", filter=Q(dataDate__gte=split)),
            views_prev=Count("id", filter=Q(dataDate__lt=split)),
        )
    )

    high = []
    medium = []
    low_count = 0

    for row in qs.iterator(chunk_size=5000):
        prev_v = int(row["views_prev"] or 0)
        last_v = int(row["views_last"] or 0)

        if last_v == 0 and prev_v >= min_views:
            high.append(row)
        elif prev_v >= min_views and last_v * 2 <= prev_v:
            medium.append(row)
        else:
            low_count += 1

    def _top(items, limit=50):
        items = sorted(items, key=lambda r: (r["views_prev"], -(r["views_last"])), reverse=True)
        out = []
        for r in items[:limit]:
            out.append(
                {
                    "subscriberCode": r["subscriberCode"],
                    "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
                    "views_prev": int(r["views_prev"] or 0),
                    "views_last": int(r["views_last"] or 0),
                }
            )
        return out

    return {
        "period": {
            "start_date": start.isoformat(),
            "end_date": today.isoformat(),
            "split_date": split.isoformat(),
            "window_days": window_days,
        },
        "summary": {
            "high_risk_users": len(high),
            "medium_risk_users": len(medium),
            "low_risk_users": low_count,
            "min_views_threshold": int(min_views),
        },
        "top": {
            "high": _top(high, limit=50),
            "medium": _top(medium, limit=50),
        },
    }

