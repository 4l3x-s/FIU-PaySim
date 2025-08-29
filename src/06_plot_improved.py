#!/usr/bin/env python3
"""
Histogram of transaction amounts with 1,000-wide bins.
- CSV: reports/hist_amounts_bins.csv  (bin_left, bin_right, bin_mid, count, is_structuring_band)
- PNG: reports/hist_amounts_log.png   (shaded 9k–10k structuring window)
"""

from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DB_PATH = ROOT / "data" / "paysim.db"
OUT_PNG = ROOT / "reports" / "hist_amounts_log.png"
OUT_CSV = ROOT / "reports" / "hist_amounts_bins.csv"

STRUCT_LO = 9000
STRUCT_HI = 10000      # excluded (right-open), aligning with regulatory threshold at 10k

def main() -> int:
    # --- load amounts (read-only)
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        df = pd.read_sql_query("SELECT amount FROM transactions", conn)

    # guard against non-positive/NaN values for log axis & binning
    a = df["amount"].to_numpy()
    a = a[np.isfinite(a)]
    a = a[a > 0]

    if a.size == 0:
        raise SystemExit("[ERROR] No positive amounts found.")

    # --- define 1,000-wide bins that include [9000, 10000)
    lo_raw, hi_raw = a.min(), a.max()
    lo = 0  # start at 0 for readability; adjust if you want a tighter floor
    # extend to include the last amount in the top bin
    hi = int(np.ceil(hi_raw / 1000.0) * 1000)
    bin_edges = np.arange(lo, hi + 1000, 1000, dtype=int)  # [lo, lo+1000, ..., hi]

    counts, edges = np.histogram(a, bins=bin_edges)
    bin_left = edges[:-1]
    bin_right = edges[1:]
    bin_mid = (bin_left + bin_right) / 2.0

    # flag the structuring band [9000, 10000)
    is_struct = ((bin_left == STRUCT_LO) & (bin_right == STRUCT_HI)).astype(int)

    # export for BI/Tableau
    out = pd.DataFrame({
        "bin_left": bin_left,
        "bin_right": bin_right,
        "bin_mid": bin_mid,
        "count": counts,
        "is_structuring_band": is_struct
    })
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    # stats for annotation
    in_band = (a >= STRUCT_LO) & (a < STRUCT_HI)
    n_band = int(in_band.sum())
    n_all = a.size
    pct_band = 100.0 * n_band / n_all if n_all else 0.0

    # --- plot
    plt.figure(figsize=(11, 6))
    plt.hist(a, bins=bin_edges)
    plt.xscale("log")  # keeps comparability with prior charts and wide ranges
    plt.xlabel("amount (log-scale)")
    plt.ylabel("count")
    plt.title("Transaction amounts (1k bins; shaded = 9k–10k)")

    # highlight the 9k–10k zone
    plt.axvspan(STRUCT_LO, STRUCT_HI, alpha=0.15)
    plt.axvline(STRUCT_LO, linestyle="--")
    plt.axvline(STRUCT_HI, linestyle="--")

    # annotation near the band (y at 90% of max bin height)
    ymax = counts.max() if counts.size else 1
    plt.text((STRUCT_LO + STRUCT_HI) / 2.0, ymax * 0.9,
             f"9k–10k\nn={n_band:,} ({pct_band:.2f}%)",
             ha="center", va="top")

    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150)
    plt.close()

    print(f"[OK] saved → {OUT_PNG}")
    print(f"[OK] bins CSV → {OUT_CSV}")
    print(f"[INFO] 9k–10k: n={n_band:,} / {n_all:,} ({pct_band:.2f}%)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())