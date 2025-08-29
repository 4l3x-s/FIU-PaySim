#!/usr/bin/env python3
from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DB_PATH = ROOT / "data" / "paysim.db"
OUT_PNG = ROOT / "reports" / "hist_amounts_log.png"

def main() -> int:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    df = pd.read_sql_query("SELECT amount FROM transactions", conn)
    conn.close()

    plt.figure(figsize=(10,6))
    plt.hist(df["amount"], bins=np.logspace(0, np.log10(df["amount"].max()), 80))
    plt.xscale("log")
    plt.xlabel("amount (log-scale)")
    plt.ylabel("count")
    plt.title("Transaction amounts (log scale)")
    plt.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=150)
    plt.close()
    print(f"[OK] saved → {OUT_PNG}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())