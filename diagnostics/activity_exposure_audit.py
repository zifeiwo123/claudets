"""Exposure audit for raw activity candidate factors.

Raw activity factors such as -volume, -amount, volume_z, and amount_z can be
liquidity, attention, or size-like structural exposures rather than clean
alpha.  This diagnostic measures their cross-sectional relationship to simple
available proxies before any candidate can be promoted.

It does NOT use final_holdout for candidate selection, does NOT restart GP,
and does NOT approve Phase 2.

Outputs:
  report/activity_exposure_audit.parquet
  report/activity_exposure_audit_summary.json
  report/activity_exposure_audit.md
  analysis/activity_exposure_audit.md
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from diagnostics.candidate_factor_matrix import (
    COST_RATE,
    MAX_STOCKS,
    RAW_ACTIVITY_FACTORS,
    compute_weekly_factor,
)
from diagnostics.followup_diagnosis import build_pivots, load_data

REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

PERIODS_DEV = {
    "train": ("2023-01-01", "2024-06-30"),
    "validation": ("2024-07-01", "2025-06-30"),
    "dev_test": ("2025-07-01", "2025-12-31"),
}
EXPOSURE_THRESHOLD = 0.50


def build_u3_universe(weekly):
    t = weekly[(weekly["trade_date"] >= "2023-01-01") & (weekly["trade_date"] <= "2025-12-31")].copy()
    t["vc"] = t["volume"] * t["close"]
    vc = t.groupby("ts_code")["vc"].mean().sort_values(ascending=False)
    n = len(vc)
    lo, hi = int(n * 0.20), int(n * 0.80)
    mid = vc.iloc[lo:hi]
    if len(mid) > MAX_STOCKS:
        mid = mid.head(MAX_STOCKS)
    return mid.index.tolist()


def period_mask(dates, start, end):
    m = dates.astype(str) >= start
    if end is not None:
        m = m & (dates.astype(str) <= end)
    return m


def weekly_spearman(signal, exposure):
    values = []
    for date in signal.index.intersection(exposure.index):
        s = signal.loc[date].dropna()
        e = exposure.loc[date].dropna()
        common = s.index.intersection(e.index)
        if len(common) < 30:
            continue
        corr = s[common].corr(e[common], method="spearman")
        if pd.notna(corr):
            values.append(float(corr))
    if not values:
        return {"mean_corr": 0.0, "median_abs_corr": 0.0, "max_abs_corr": 0.0, "weeks": 0}
    arr = np.array(values, dtype=float)
    return {
        "mean_corr": float(round(arr.mean(), 6)),
        "median_abs_corr": float(round(np.median(np.abs(arr)), 6)),
        "max_abs_corr": float(round(np.max(np.abs(arr)), 6)),
        "weeks": int(len(arr)),
    }


def compute_all():
    weekly, _, _ = load_data()
    universe = build_u3_universe(weekly)
    pivots = build_pivots(weekly, universe, ["close", "volume", "amount"])
    close = pivots["close"]
    volume = pivots["volume"]
    amount = pivots["amount"]

    exposures = {
        "log_volume": np.log(volume.replace(0, np.nan)),
        "log_amount": np.log(amount.replace(0, np.nan)),
        "log_vol_close": np.log((volume * close).replace(0, np.nan)),
        "price_level": close,
        "ret_4w": close.pct_change(4, fill_method=None),
    }

    rows = []
    for factor_name in RAW_ACTIVITY_FACTORS:
        factor = compute_weekly_factor({"close": close, "volume": volume, "amount": amount}, factor_name)
        for period, (start, end) in PERIODS_DEV.items():
            f_period = factor[period_mask(factor.index, start, end)]
            for exposure_name, exposure in exposures.items():
                e_period = exposure[exposure.index.isin(f_period.index)]
                stats = weekly_spearman(f_period, e_period)
                rows.append({
                    "period": period,
                    "factor": factor_name,
                    "exposure": exposure_name,
                    **stats,
                    "flagged": bool(stats["median_abs_corr"] >= EXPOSURE_THRESHOLD),
                })

    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(REPORT_DIR, "activity_exposure_audit.parquet"))

    factor_flags = []
    for factor_name, sub in df.groupby("factor"):
        max_med = float(sub["median_abs_corr"].max())
        flagged_exposures = sorted(sub.loc[sub["flagged"], "exposure"].unique().tolist())
        factor_flags.append({
            "factor": factor_name,
            "max_median_abs_corr": round(max_med, 6),
            "flagged_exposures": flagged_exposures,
            "promotion_allowed": False,
            "reason": (
                "raw activity factors are blocked from promotion until neutralized "
                "or separately justified with richer exposure data"
            ),
        })

    summary = {
        "generated_at": datetime.now().isoformat(),
        "universe": "frozen_development_universe: U3_volclose_mid60, 2023-01-01 to 2025-12-31",
        "periods": PERIODS_DEV,
        "exposure_threshold_median_abs_corr": EXPOSURE_THRESHOLD,
        "cost_rate_context": COST_RATE,
        "factor_flags": factor_flags,
        "raw_activity_gate": "blocked_pending_neutralization_or_richer_exposure_audit",
        "final_holdout_used": False,
        "gp_status": "paused",
        "phase2_status": "paused",
    }
    with open(os.path.join(REPORT_DIR, "activity_exposure_audit_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return df, summary


def generate_report(df, summary):
    rows = []
    for f in summary["factor_flags"]:
        rows.append(
            f"| {f['factor']} | {f['max_median_abs_corr']:.2f} | "
            f"{', '.join(f['flagged_exposures']) if f['flagged_exposures'] else 'none'} | "
            f"{'Y' if f['promotion_allowed'] else 'N'} |"
        )

    top = df.sort_values("median_abs_corr", ascending=False).head(20)
    detail_rows = "\n".join(
        f"| {r['period']} | {r['factor']} | {r['exposure']} | "
        f"{r['mean_corr']:+.2f} | {r['median_abs_corr']:.2f} | {r['weeks']} | "
        f"{'Y' if r['flagged'] else 'N'} |"
        for _, r in top.iterrows()
    )

    report = f"""# raw activity exposure audit

**Generated**: {summary['generated_at']}
**GP**: {summary['gp_status']}
**Phase 2**: {summary['phase2_status']}

> Raw activity factors are not clean alpha candidates by default.  This audit
> checks whether they are dominated by liquidity, attention, or price-level
> proxies before any promotion decision.

---

## 1. Gate Result

| Item | Status |
|------|--------|
| Raw activity gate | {summary['raw_activity_gate']} |
| Final holdout used | {summary['final_holdout_used']} |
| Universe | {summary['universe']} |
| Threshold | median abs Spearman >= {summary['exposure_threshold_median_abs_corr']:.2f} |

## 2. Factor Flags

| Factor | Max Median Abs Corr | Flagged Exposures | Promotion Allowed? |
|--------|---------------------|-------------------|--------------------|
{chr(10).join(rows)}

## 3. Strongest Exposure Relationships

| Period | Factor | Exposure | Mean Corr | Median Abs Corr | Weeks | Flagged |
|--------|--------|----------|-----------|-----------------|-------|---------|
{detail_rows}

## 4. Interpretation

Raw activity candidates remain blocked from promotion unless a later audit
adds richer controls such as market capitalization, industry, liquidity, and
turnover neutralization.  This does not invalidate the frozen `-volume`
baseline; it prevents treating similar raw activity signals as newly promoted
model features.

## 5. Generated Files

| File | Location |
|------|----------|
| Parquet | report/activity_exposure_audit.parquet |
| Summary JSON | report/activity_exposure_audit_summary.json |
| Report | report/activity_exposure_audit.md |
| Report (analysis) | analysis/activity_exposure_audit.md |
| Script | diagnostics/activity_exposure_audit.py |
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        with open(os.path.join(d, "activity_exposure_audit.md"), "w", encoding="utf-8") as f:
            f.write(report)


def main():
    df, summary = compute_all()
    generate_report(df, summary)
    flagged = sum(1 for f in summary["factor_flags"] if f["flagged_exposures"])
    print(f"Rows: {len(df)}")
    print(f"Raw activity factors with flagged exposures: {flagged}/{len(summary['factor_flags'])}")
    print(f"Raw activity gate: {summary['raw_activity_gate']}")
    print(f"GP: {summary['gp_status']}, Phase 2: {summary['phase2_status']}")


if __name__ == "__main__":
    main()
