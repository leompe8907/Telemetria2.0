import csv
import sys
from collections import Counter
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python top_channels_csv.py <path-to-csv> [top_n]")
        raise SystemExit(2)

    p = Path(sys.argv[1])
    top_n = int(sys.argv[2]) if len(sys.argv) >= 3 else 20

    ctr = Counter()
    rows = 0
    missing = 0

    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows += 1
            name = (row.get("dataName") or "").strip().strip('"')
            if not name:
                missing += 1
                continue
            ctr[name] += 1

    print("rows", rows)
    print("dataName_missing", missing)
    print("unique_channels", len(ctr))
    print("\nTOP {}:".format(top_n))
    for name, count in ctr.most_common(top_n):
        print("{}\t{}".format(count, name))

    items = ctr.most_common()
    if items:
        mid = items[len(items) // 2]
        low = items[-1]
        print("\nSUGGESTIONS:")
        print("high5:", ", ".join([x[0] for x in items[:5]]))
        print("mid_example:", mid[0], mid[1])
        print("low_example:", low[0], low[1])


if __name__ == "__main__":
    main()

