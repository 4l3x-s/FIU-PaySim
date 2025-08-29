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

# Direct connection, no extra checks
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

sql = """
    SELECT
        (step - 1) / 24          AS day_num,
        (step - 1) % 24          AS hour_of_day,
        COUNT(*)                 AS n
    FROM transactions
    WHERE type IN ('CASH_IN','PAYMENT','TRANSFER')
      AND amount BETWEEN 9000 AND 9999.99
    GROUP BY day_num, hour_of_day
    ORDER BY day_num, hour_of_day;
"""
df = pd.read_sql_query(sql, conn)

pivot = df.pivot(index="hour_of_day", columns="day_num", values="n").fillna(0)

plt.figure(figsize=(12, 6))
sns.heatmap(pivot, cmap="Reds")
plt.xlabel("day_num (0-based)")
plt.ylabel("hour_of_day (0..23)")
plt.title("Near-threshold activity (9,000–9,999.99) by day × hour")
plt.tight_layout()

out_png = (DB_PATH.parent.parent / "reports" / "heatmap_near_threshold.png")
out_png.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_png, dpi=150)
print(f"[OK] Heatmap saved to {out_png}")