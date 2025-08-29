#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FEAT_PATH = ROOT / "data" / "features_accounts.parquet"
OUT_CSV = ROOT / "reports" / "anomalies_accounts.csv"

NUM_COLS = [
    "n_tx","amt_sum","amt_mean","amt_max","near_n","near_pct",
    "ia_mean","ia_median","ia_std","cp_diversity"
]

def main() -> int:
    if not FEAT_PATH.exists():
        raise SystemExit(f"[ERROR] features not found: {FEAT_PATH}. Run 03_features_accounts.py first.")

    df = pd.read_parquet(FEAT_PATH)
    X = df[NUM_COLS].fillna(0.0).to_numpy()
    Xs = StandardScaler().fit_transform(X)

    # tweak contamination by how many you want to review
    model = IsolationForest(n_estimators=300, contamination=0.005, random_state=42)
    scores = model.fit_predict(Xs)              # -1 anomaly, 1 normal
    iso_score = model.decision_function(Xs)     # lower = more anomalous

    out = df[["account"] + NUM_COLS].copy()
    out["iso_score"] = iso_score
    out["is_anom"] = (scores == -1)

    out.sort_values("iso_score", ascending=True, inplace=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"[OK] anomalies saved → {OUT_CSV} (top rows are most anomalous)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())