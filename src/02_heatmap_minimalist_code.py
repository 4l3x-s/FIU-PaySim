#!/usr/bin/env python3
from pathlib import Path
import sqlite3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ---------- Paths ----------
HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DB_PATH = ROOT / "data" / "paysim.db"
OUT_DIR = ROOT / "reports"
OUT_PNG = OUT_DIR / "heatmap_near_threshold.png"

# --- SQL: near-threshold activity (9,000–9,999.99) for CASH_IN/PAYMENT/TRANSFER ---
SQL = """
SELECT
  (step - 1) / 24  AS day_num,      -- 0..30
  (step - 1) % 24  AS hour_of_day,  -- 0..23
  COUNT(*)         AS n
FROM transactions
WHERE type IN ('CASH_IN','PAYMENT','TRANSFER')
  AND amount BETWEEN 9000 AND 9999.99
GROUP BY day_num, hour_of_day
ORDER BY day_num, hour_of_day;
"""

def main() -> int:
    # 1) Connect read-only (safe), run query
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    df = pd.read_sql_query(SQL, conn)
    conn.close()

    # 2) Pivot to hour (rows) × day (cols)
    pivot = df.pivot(index="hour_of_day", columns="day_num", values="n").fillna(0)

    # 3) Plot (simple, consistent look)
    plt.figure(figsize=(12, 6))
    ax = sns.heatmap(pivot, cmap="Reds")
    ax.set_xlabel("day_num (0-based)")
    ax.set_ylabel("hour_of_day (0..23)")
    ax.set_title("Near-threshold activity (9,000–9,999.99) by day × hour")
    plt.tight_layout()

    # 4) Save PNG (no plt.show() → avoids backend popups/errors)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150)
    plt.close()

    print(f"[OK] Heatmap saved → {OUT_PNG}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())