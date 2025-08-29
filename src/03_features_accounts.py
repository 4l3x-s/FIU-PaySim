#!/usr/bin/env python3
"""
Build per-account features from PaySim (SQLite -> CSV/Parquet).
"""

from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

# ---------- Paths ----------
HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DB_PATH = ROOT / "data" / "paysim.db"
OUT_DIR = ROOT / "data"
OUT_CSV = OUT_DIR / "features_accounts.csv"
OUT_PARQ = OUT_DIR / "features_accounts.parquet"

# ---------- SQL ----------
SQL = """
SELECT
  step,
  (step - 1) / 24       AS day_num,
  (step - 1) % 24       AS hour_of_day,
  type,
  amount,
  nameOrig,
  nameDest,
  isFraud,
  isFlaggedFraud
FROM transactions
"""

# ---------- Helpers ----------
def interarrival_stats_steps(s: pd.Series) -> pd.Series:
    a = s.sort_values().to_numpy()
    if a.size < 2:
        return pd.Series({"ia_mean": np.nan, "ia_median": np.nan, "ia_std": np.nan})
    d = np.diff(a)
    return pd.Series({
        "ia_mean": float(d.mean()),
        "ia_median": float(np.median(d)),
        "ia_std": float(d.std(ddof=1)) if d.size > 1 else 0.0,
    })

def round_trip_flag(df: pd.DataFrame) -> pd.Series:
    sent = df.groupby("nameOrig")["nameDest"].apply(set)
    recv = df.groupby("nameDest")["nameOrig"].apply(set)
    idx = sent.index.union(recv.index)
    out = pd.Series(False, index=idx, name="round_trip_any")
    for acc in idx:
        s = sent.get(acc, set())
        r = recv.get(acc, set())
        out.loc[acc] = len(s & r) > 0
    # ensure index has a name for joins
    out.index.name = "nameOrig"
    return out

# ---------- Main ----------
def main() -> int:
    if not DB_PATH.exists():
        raise SystemExit(f"[ERROR] DB not found at {DB_PATH}. Run 01_load_to_sqlite.py first.")

    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        df = pd.read_sql_query(SQL, conn)

    # focus on customer-originated accounts
    df["is_customer_orig"] = df["nameOrig"].str.startswith("C")
    df_cust = df[df["is_customer_orig"]].copy()
    df_cust["near_thresh"] = df_cust["amount"].between(9000, 9999.99).astype(int)

    # aggregates
    agg = df_cust.groupby("nameOrig").agg(
        n_tx=("amount", "size"),
        amt_sum=("amount", "sum"),
        amt_mean=("amount", "mean"),
        amt_max=("amount", "max"),
        near_n=("near_thresh", "sum"),
        fraud_n=("isFraud", "sum"),
        flagged_n=("isFlaggedFraud", "sum"),
    )
    agg["near_pct"] = agg["near_n"] / agg["n_tx"].clip(lower=1)
    agg.index.name = "nameOrig"  # <-- normalize index name

    # inter-arrival
    ia = (
        df_cust.groupby("nameOrig")["step"]
        .apply(interarrival_stats_steps)
        .unstack()  # columns: ia_mean, ia_median, ia_std
    )
    ia.index.name = "nameOrig"  # <-- normalize

    # counterparty diversity
    cp_div = (
        df_cust.groupby("nameOrig")["nameDest"]
        .nunique()
        .rename("cp_diversity")
    )
    cp_div.index.name = "nameOrig"  # <-- normalize

    # round-trip heuristic (uses full df to consider both directions)
    rt = round_trip_flag(df)        # already named and indexed

    # join all
    features = (
        agg.join(ia, how="left")
        .join(cp_div, how="left")
        .join(rt, how="left")
        .fillna({"cp_diversity": 0, "round_trip_any": False})
        .reset_index(names="account")
    )

    # write outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUT_CSV, index=False)
    features.to_parquet(OUT_PARQ, index=False)
    print(f"[OK] wrote features: {OUT_CSV} and {OUT_PARQ}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())