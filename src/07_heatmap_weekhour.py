#!/usr/bin/env python3
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DB_PATH = ROOT / "data" / "paysim.db"
OUT_PNG = ROOT / "reports" / "heatmap_weekday_hour.png"

SQL = """
-- Compute weekday (0=Mon … 6=Sun) and hour-of-day (0..23)
SELECT
  ((step-1)/24) % 7       AS weekday,
  (step-1) % 24           AS hour_of_day,
  COUNT(*)                AS n
FROM transactions
GROUP BY weekday, hour_of_day
ORDER BY weekday, hour_of_day;
"""

def main() -> int:
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        df = pd.read_sql_query(SQL, conn)

    # pivot to 7x24 matrix (rows=weekday, cols=hour)
    mat = df.pivot(index="weekday", columns="hour_of_day", values="n").fillna(0).to_numpy()
    # order labels
    wd_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    hr_labels = [f"{h:02d}:00" for h in range(24)]

    plt.figure(figsize=(11, 5.5))
    im = plt.imshow(mat, aspect="auto", cmap="Blues", origin="upper")
    plt.colorbar(im, label="transaction count")
    plt.xticks(np.arange(24), hr_labels, rotation=90)
    plt.yticks(np.arange(7), wd_labels)
    plt.xlabel("Hour of day")
    plt.ylabel("Weekday")
    plt.title("Weekday × Hour Activity Heatmap (all transactions)")

    # annotate max cell for a quick narrative hook
    w_i, h_i = np.unravel_index(np.argmax(mat), mat.shape)
    plt.scatter([h_i],[w_i], marker="o", s=80, edgecolor="black", facecolor="none", linewidths=1.2)
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150)
    plt.close()
    print(f"[OK] saved → {OUT_PNG}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())