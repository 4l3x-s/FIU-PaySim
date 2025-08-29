#!/usr/bin/env python3
"""
Load PaySim CSV -> SQLite

Features:
- Robust path handling (works from any CWD; script or console).
- WAL + synchronous=NORMAL to speed up bulk ingest safely.
- Auto-avoid SQLite's ~999-parameter limit.
- Chunked streaming to keep memory stable on 6.3M rows.
- Clear logging + verification COUNT(*).

Outputs:
- data/paysim.db (table: transactions)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


def resolve_project_root() -> Path:
    """Return project root (parent of src/) whether run as script or in console."""
    try:
        return Path(__file__).resolve().parents[1]
    except NameError:
        # Running in a console / REPL (no __file__)
        print("[WARN] __file__ not defined; using current working directory.")
        return Path.cwd()


def safe_insert_params(n_cols: int, sqlite_param_limit: int = 999) -> int:
    """
    Compute safe maximum rows per multi-row INSERT for SQLite, given column count.
    If result < 1, return 1 to avoid zero/negative edge cases.
    """
    return max(1, sqlite_param_limit // max(1, n_cols))


def main() -> int:
    t0 = time.time()

    # ----- Paths -----
    ROOT = resolve_project_root()
    DATA_DIR = ROOT / "data"
    CSV_PATH = DATA_DIR / "PS_20174392719_1491204439457_log.csv"
    DB_PATH = DATA_DIR / "paysim.db"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        print(f"[ERROR] CSV not found: {CSV_PATH}")
        print("Place the PaySim CSV in the 'data/' folder and retry.")
        return 1

    # ----- Load CSV (streaming read optional; here full read is OK on modern Macs) -----
    print(f"[1/4] Loading CSV: {CSV_PATH.name}")
    df = pd.read_csv(CSV_PATH)
    print(f"    -> {len(df):,} rows, {len(df.columns)} columns")
    print(f"    -> columns: {list(df.columns)}")

    # Decide insertion strategy to avoid SQLite's 999-parameter limit
    n_cols = len(df.columns)
    max_multi_rows = safe_insert_params(n_cols)  # with 11 cols -> 90 rows max
    # We'll use executemany (method=None), which never hits the limit,
    # but keep the computed value in case you want to try method="multi".
    print(f"[Info] SQLite param limit handling: columns={n_cols}, "
          f"max_multi_rows_if_used={max_multi_rows}")

    # Chunk size: large enough to be fast, small enough to keep memory stable.
    # For executemany, this controls how many rows are sent per batch.
    CHUNK = 50_000

    # ----- Create DB engine -----
    print(f"[2/4] Creating SQLite DB at: {DB_PATH}")
    engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

    # Speed tweaks for bulk load (safe defaults for local dev):
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
        conn.exec_driver_sql("PRAGMA temp_store=MEMORY;")
        conn.exec_driver_sql("PRAGMA mmap_size=30000000000;")  # best-effort; ignored if not supported

    # ----- Write to SQLite (chunked, executemany) -----
    print(f"[3/4] Writing table 'transactions' (chunksize={CHUNK}, executemany)…")
    t_write = time.time()
    df.to_sql(
        "transactions",
        engine,
        if_exists="replace",
        index=False,
        chunksize=CHUNK,
        method=None,  # executemany -> avoids 999-parameter limit cleanly
    )
    print(f"    -> write completed in {time.time() - t_write:,.1f}s")

    # ----- Verify -----
    print("[4/4] Verifying row count…")
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar_one()
    print(f"    -> COUNT(*) = {total:,}")

    print(f"✅ Done in {time.time() - t0:,.1f}s. Database ready at: {DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# connect to your SQLite DB
conn = sqlite3.connect("/Users/alejandrosoba/Documents/FIU-PaySim/data/paysim.db")

# now run your SQL query
df = pd.read_sql_query("""
    SELECT day_num, hour_of_day, COUNT(*) AS n
    FROM v_transactions
    WHERE type IN ('CASH_IN','PAYMENT','TRANSFER')
      AND amount BETWEEN 9000 AND 9999.99
    GROUP BY day_num, hour_of_day
    ORDER BY day_num, hour_of_day;
""", conn)

# pivot for heatmap
pivot = df.pivot(index="hour_of_day", columns="day_num", values="n")

# plot
sns.heatmap(pivot, cmap="Reds")
plt.show()
