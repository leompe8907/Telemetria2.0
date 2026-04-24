import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def parse_args():
    ap = argparse.ArgumentParser(description="Backtest simple forecast per channel from CSV export.")
    ap.add_argument("--csv", required=True, help="Path to telemetryrecords_*.csv")
    ap.add_argument("--channels", required=True, help="Comma-separated channel names (dataName/streamName)")
    ap.add_argument("--horizon", type=int, default=7, help="Forecast horizon in days (default 7)")
    ap.add_argument("--min_train_days", type=int, default=30, help="Min training days required")
    ap.add_argument("--use_stream_name_fallback", action="store_true", help="When dataName empty, parse data JSON for streamName")
    return ap.parse_args()


def _safe_parse_dt(s: str):
    if not s:
        return None
    s = s.strip().strip('"')
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        # best effort
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                pass
    return None


def _extract_stream_name(data_field: str):
    if not data_field:
        return None
    data_field = data_field.strip()
    # CSV field comes like: "{""streamId"":262,""streamName"":""HGTV""}"
    # Convert doubled quotes to normal quotes.
    try:
        s = data_field
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        s = s.replace('""', '"')
        obj = json.loads(s)
        name = obj.get("streamName")
        return name.strip() if isinstance(name, str) and name.strip() else None
    except Exception:
        return None


def build_daily_series(csv_path: Path, channels_set: set[str], use_stream_name_fallback: bool):
    """
    Returns a dict channel -> list[(date_iso, views)] with continuous days filled with 0.
    """
    counts_by_day = defaultdict(lambda: defaultdict(int))
    min_day = {}
    max_day = {}

    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            dt = _safe_parse_dt(row.get("timestamp") or "")
            if dt is None:
                continue
            day = dt.date()

            name = (row.get("dataName") or "").strip().strip('"')
            if not name and use_stream_name_fallback:
                name = _extract_stream_name(row.get("data") or "") or ""

            if not name or name not in channels_set:
                continue

            counts_by_day[name][day] += 1
            if name not in min_day or day < min_day[name]:
                min_day[name] = day
            if name not in max_day or day > max_day[name]:
                max_day[name] = day

    series: dict[str, list[tuple[str, float]]] = {}
    for ch in channels_set:
        if ch not in min_day:
            continue
        start = min_day[ch]
        end = max_day[ch]
        cur = start
        out = []
        from datetime import timedelta

        while cur <= end:
            out.append((cur.isoformat(), float(counts_by_day[ch].get(cur, 0))))
            cur = cur + timedelta(days=1)
        series[ch] = out

    return series


def fit_trend_forecast(train_values: list[float], horizon: int):
    """
    Baseline "training": linear trend over time index.
    Returns forecast array length horizon, plus fitted slope/intercept.
    """
    n = len(train_values)
    if n < 2:
        slope = 0.0
        intercept = float(train_values[-1]) if n else 0.0
    else:
        # Simple linear regression y = a*x + b
        xs = list(range(n))
        x_mean = (n - 1) / 2.0
        y_mean = sum(train_values) / n
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, train_values))
        den = sum((x - x_mean) ** 2 for x in xs) or 1.0
        slope = num / den
        intercept = y_mean - slope * x_mean

    pred = []
    for i in range(n, n + horizon):
        v = slope * i + intercept
        if v < 0:
            v = 0.0
        pred.append(float(v))
    return pred, float(slope), float(intercept)


def metrics(y_true: list[float], y_pred: list[float]):
    n = max(len(y_true), 1)
    abs_err = [abs(a - b) for a, b in zip(y_true, y_pred)]
    mae = sum(abs_err) / n
    rmse = (sum((a - b) ** 2 for a, b in zip(y_true, y_pred)) / n) ** 0.5
    mape_terms = []
    for a, b in zip(y_true, y_pred):
        if a == 0:
            continue
        mape_terms.append(abs((a - b) / a))
    mape = (sum(mape_terms) / len(mape_terms) * 100.0) if mape_terms else 0.0
    return {"mae": mae, "rmse": rmse, "mape": mape}


def backtest_one(series: list[tuple[str, float]], horizon: int, min_train_days: int):
    """
    Single holdout: train all but last horizon days; test on last horizon days.
    """
    if len(series) < (min_train_days + horizon):
        return None

    train = series[: -horizon]
    test = series[-horizon:]

    train_y = [v for _, v in train]
    test_y = [v for _, v in test]
    pred, slope, intercept = fit_trend_forecast(train_y, horizon=horizon)
    m = metrics(test_y, pred)

    return {
        "train_start": train[0][0],
        "train_end": train[-1][0],
        "test_start": test[0][0],
        "test_end": test[-1][0],
        "model": {"type": "linear_trend", "slope": slope, "intercept": intercept},
        "metrics": m,
        "test_actual_sum": float(sum(test_y)),
        "test_pred_sum": float(sum(pred)),
    }


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]
    channels_set = set(channels)

    series_by_channel = build_daily_series(
        csv_path=csv_path,
        channels_set=channels_set,
        use_stream_name_fallback=args.use_stream_name_fallback,
    )

    results = {"horizon_days": args.horizon, "channels": {}, "skipped": []}

    for ch in channels:
        s = series_by_channel.get(ch)
        if not s:
            results["skipped"].append({"channel": ch, "reason": "NO_DATA"})
            continue
        r = backtest_one(s, horizon=args.horizon, min_train_days=args.min_train_days)
        if r is None:
            results["skipped"].append({"channel": ch, "reason": "INSUFFICIENT_DAYS", "days": int(len(s))})
            continue
        results["channels"][ch] = r

    # Print a concise summary
    print("Backtest horizon:", args.horizon, "days")
    for ch, r in results["channels"].items():
        m = r["metrics"]
        print(
            f"{ch}\tMAE={m['mae']:.3f}\tRMSE={m['rmse']:.3f}\tMAPE={m['mape']:.2f}%"
        )
    if results["skipped"]:
        print("\nSkipped:")
        for it in results["skipped"]:
            print(it)

    out_path = csv_path.with_suffix(f".backtest_h{args.horizon}.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nWrote:", str(out_path))


if __name__ == "__main__":
    main()

