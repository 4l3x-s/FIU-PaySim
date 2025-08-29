#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FEAT_PATH = ROOT / "data" / "features_accounts.parquet"
OUT_TXT = ROOT / "reports" / "hypothesis_tests.txt"

def main() -> int:
    if not FEAT_PATH.exists():
        raise SystemExit(f"[ERROR] features not found: {FEAT_PATH}")

    df = pd.read_parquet(FEAT_PATH)
    # “Flagged” means account ever had isFlaggedFraud in its outgoing txs
    flagged = df[df["flagged_n"] > 0]["near_pct"].dropna().to_numpy()
    clean   = df[df["flagged_n"] == 0]["near_pct"].dropna().to_numpy()

    # If either side is empty, bail early
    if len(flagged) < 5 or len(clean) < 5:
        raise SystemExit("[WARN] Not enough accounts per group to test.")

    t_res = stats.ttest_ind(flagged, clean, equal_var=False)
    mw_res = stats.mannwhitneyu(flagged, clean, alternative="two-sided")

    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TXT.open("w") as f:
        f.write(f"Flagged n={len(flagged)}, Clean n={len(clean)}\n")
        f.write(f"T-test (Welch): stat={t_res.statistic:.4f}, p={t_res.pvalue:.4g}\n")
        f.write(f"Mann-Whitney U: stat={mw_res.statistic:.4f}, p={mw_res.pvalue:.4g}\n")

    print(f"[OK] wrote results → {OUT_TXT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())