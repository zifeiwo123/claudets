"""Candidate factor matrix: evaluate simple factor families vs frozen baseline.

Tests candidate factors on train / validation / dev_test periods only.
Final holdout is reported only for the frozen baseline, not used for
selecting new factors.  Every candidate is compared to universe EW and
to the frozen simple baseline.

Candidate families:
  weekly reversal:  -ret_1w, -ret_4w, -ret_12w
  weekly volatility: -vol_4w, -vol_12w
  weekly activity:   -volume, -amount, volume_z, amount_z
  daily-derived:     d_ret_5d, d_ret_20d, d_vol_20d, d_downside_vol_20d,
                     d_range_20d, d_intraday_strength_5d,
                     d_volume_z20, d_amount_z20

Outputs:
  report/candidate_factor_matrix.parquet
  report/candidate_factor_matrix_summary.json
  report/candidate_factor_matrix.md
  analysis/candidate_factor_matrix.md
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

from diagnostics.followup_diagnosis import (
    build_long_only_portfolio,
    build_pivots,
    compute_fwd_ret,
    load_data,
    portfolio_metrics,
)

REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"
COST_RATE = 0.004
MAX_STOCKS = 400

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

PERIODS_DEV = {
    "train": ("2023-01-01", "2024-06-30"),
    "validation": ("2024-07-01", "2025-06-30"),
    "dev_test": ("2025-07-01", "2025-12-31"),
}
FINAL_HOLDOUT = ("2026-01-01", None)

# -- candidate families --
CANDIDATE_FACTORS = {
    "weekly_reversal": {
        "-ret_1w": "close.pct_change(1) * -1",
        "-ret_4w": "close.pct_change(4) * -1",
        "-ret_12w": "close.pct_change(12) * -1",
    },
    "weekly_volatility": {
        "-vol_4w": "ret.rolling(4).std() * -1",
        "-vol_12w": "ret.rolling(12).std() * -1",
    },
    "weekly_activity": {
        "-volume": "-1 * volume",
        "-amount": "-1 * amount",
        "volume_z": "(volume - volume.rolling(20).mean()) / volume.rolling(20).std()",
        "amount_z": "(amount - amount.rolling(20).mean()) / amount.rolling(20).std()",
    },
}

# -- frozen baseline factors --
BASELINE_FACTORS = ["-volume", "-ret_4w"]


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


def compute_weekly_factor(pivots, name):
    """Compute simple candidate factor from pivot tables. Returns DataFrame."""
    c = pivots["close"]
    v = pivots["volume"]
    a = pivots["amount"]
    ret = c.pct_change(fill_method=None)

    if name == "-ret_1w":
        return -ret
    elif name == "-ret_4w":
        return -c.pct_change(4, fill_method=None)
    elif name == "-ret_12w":
        return -c.pct_change(12, fill_method=None)
    elif name == "-vol_4w":
        return -ret.rolling(4, min_periods=2).std()
    elif name == "-vol_12w":
        return -ret.rolling(12, min_periods=4).std()
    elif name == "-volume":
        return -v
    elif name == "-amount":
        return -a
    elif name == "volume_z":
        r = v.rolling(20, min_periods=10)
        return (v - r.mean()) / (r.std() + 1e-10)
    elif name == "amount_z":
        r = a.rolling(20, min_periods=10)
        return (a - r.mean()) / (r.std() + 1e-10)
    else:
        raise ValueError(f"Unknown factor: {name}")


def compute_daily_derived_factor(pivots, name):
    """Use daily-derived features already in the pivot."""
    return pivots.get(name)


def evaluate_factor(factor_df, fwd_df, pname, factor_name, top_n, family, label):
    m = period_mask(factor_df.index, *PERIODS_DEV[pname])
    fp = factor_df[m]
    fwp = fwd_df[fwd_df.index.isin(fp.index)]
    if len(fp) < 5:
        return None
    pf = build_long_only_portfolio(fp, fwp, n_stocks=top_n, cost_rate=COST_RATE)
    if len(pf) < 3:
        return None
    m_abs = portfolio_metrics(pf["net_ret"])
    ew = fwp.mean(axis=1)
    ci = pf.index.intersection(ew.index)
    excess = pf["net_ret"][ci] - ew[ci]
    m_exc = portfolio_metrics(excess)
    m_ew = portfolio_metrics(ew)
    return {
        "period": pname,
        "family": family,
        "label": label,
        "factor": factor_name,
        "top_n": top_n,
        "weeks": int(len(pf)),
        "abs_annual_return": float(round(m_abs["annual_return"], 6)),
        "abs_sharpe": float(round(m_abs["sharpe"], 4)),
        "abs_max_drawdown": float(round(m_abs["max_drawdown"], 6)),
        "univ_ew_annual_return": float(round(m_ew["annual_return"], 6)),
        "excess_annual_return": float(round(m_exc["annual_return"], 6)),
        "ir_vs_ew": float(round(m_exc["sharpe"], 4)),
        "excess_max_drawdown": float(round(m_exc["max_drawdown"], 6)),
        "excess_win_rate": float(round(m_exc["win_rate"], 4)),
        "turnover": float(round(pf["turnover"].mean(), 4)),
        "annualized_cost": float(round(pf["turnover"].mean() * COST_RATE * 52, 4)),
    }


def evaluate_holdout_baseline(factor_df, fwd_df, factor_name, top_n, label):
    """Frozen baseline only on final holdout."""
    m = period_mask(factor_df.index, *FINAL_HOLDOUT)
    fp = factor_df[m]
    fwp = fwd_df[fwd_df.index.isin(fp.index)]
    if len(fp) < 5:
        return None
    pf = build_long_only_portfolio(fp, fwp, n_stocks=top_n, cost_rate=COST_RATE)
    if len(pf) < 3:
        return None
    m_abs = portfolio_metrics(pf["net_ret"])
    ew = fwp.mean(axis=1)
    ci = pf.index.intersection(ew.index)
    excess = pf["net_ret"][ci] - ew[ci]
    m_exc = portfolio_metrics(excess)
    m_ew = portfolio_metrics(ew)
    return {
        "period": "final_holdout",
        "family": "frozen_baseline",
        "label": label,
        "factor": factor_name,
        "top_n": top_n,
        "weeks": int(len(pf)),
        "abs_annual_return": float(round(m_abs["annual_return"], 6)),
        "abs_sharpe": float(round(m_abs["sharpe"], 4)),
        "abs_max_drawdown": float(round(m_abs["max_drawdown"], 6)),
        "univ_ew_annual_return": float(round(m_ew["annual_return"], 6)),
        "excess_annual_return": float(round(m_exc["annual_return"], 6)),
        "ir_vs_ew": float(round(m_exc["sharpe"], 4)),
        "excess_max_drawdown": float(round(m_exc["max_drawdown"], 6)),
        "excess_win_rate": float(round(m_exc["win_rate"], 4)),
        "turnover": float(round(pf["turnover"].mean(), 4)),
        "annualized_cost": float(round(pf["turnover"].mean() * COST_RATE * 52, 4)),
    }


def compute_all():
    weekly, _, _ = load_data()
    universe = build_u3_universe(weekly)

    # Pivots for weekly factors
    wpivots = build_pivots(weekly, universe, ["close", "high", "low", "volume", "amount"])
    # Pivots for daily-derived factors
    fpivots = {}
    daily_fields = ["d_ret_5d", "d_ret_20d", "d_vol_20d", "d_downside_vol_20d",
                    "d_range_20d", "d_intraday_strength_5d", "d_volume_z20", "d_amount_z20"]
    w = weekly[weekly["ts_code"].isin(universe)].copy()
    for f in daily_fields:
        if f in w.columns:
            piv = w.pivot_table(index="trade_date", columns="ts_code", values=f, aggfunc="last")
            fpivots[f] = piv.sort_index()

    fwd_full = compute_fwd_ret(wpivots["close"])

    results = []

    # Evaluate weekly candidate families
    for family, factors in CANDIDATE_FACTORS.items():
        for fname in factors:
            factor = compute_weekly_factor(wpivots, fname)
            for pname in PERIODS_DEV:
                for top_n in [50, 100]:
                    r = evaluate_factor(factor, fwd_full, pname, fname, top_n, family, "candidate")
                    if r:
                        results.append(r)

    # Evaluate daily-derived features as raw factors
    for fname in daily_fields:
        if fname not in fpivots:
            continue
        factor = fpivots[fname]
        for pname in PERIODS_DEV:
            for top_n in [50, 100]:
                r = evaluate_factor(factor, fwd_full, pname, fname, top_n, "daily_derived", "candidate")
                if r:
                    results.append(r)

    # Evaluate frozen baselines on dev periods AND final holdout
    for fname in BASELINE_FACTORS:
        factor = compute_weekly_factor(wpivots, fname)
        for pname in PERIODS_DEV:
            for top_n in [50, 100]:
                r = evaluate_factor(factor, fwd_full, pname, fname, top_n, "frozen_baseline", "baseline")
                if r:
                    results.append(r)
        # final holdout: only for baseline
        for top_n in [50, 100]:
            r = evaluate_holdout_baseline(factor, fwd_full, fname, top_n, "baseline")
            if r:
                results.append(r)

    df = pd.DataFrame(results)
    df.to_parquet(os.path.join(REPORT_DIR, "candidate_factor_matrix.parquet"))

    # Summary JSON
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_candidates": int(len(df[df["label"] == "candidate"])),
        "total_baseline_rows": int(len(df[df["label"] == "baseline"])),
        "dev_periods": list(PERIODS_DEV.keys()),
        "best_candidate_vs_baseline": {},
        "gp_status": "paused",
        "phase2_status": "paused",
    }

    # For each dev period + top_n, find best candidate IR vs EW
    for pname in PERIODS_DEV:
        for top_n in [50, 100]:
            key = f"{pname}_LO{top_n}"
            cand = df[(df["period"] == pname) & (df["label"] == "candidate") & (df["top_n"] == top_n)]
            base = df[(df["period"] == pname) & (df["label"] == "baseline") & (df["top_n"] == top_n)]
            if len(cand) > 0 and len(base) > 0:
                best_c = cand.loc[cand["ir_vs_ew"].idxmax()]
                best_b = base.loc[base["ir_vs_ew"].idxmax()]
                beats = best_c["ir_vs_ew"] > best_b["ir_vs_ew"]
                summary["best_candidate_vs_baseline"][key] = {
                    "best_candidate_factor": best_c["factor"],
                    "best_candidate_family": best_c["family"],
                    "best_candidate_ir": best_c["ir_vs_ew"],
                    "best_baseline_factor": best_b["factor"],
                    "best_baseline_ir": best_b["ir_vs_ew"],
                    "candidate_beats_baseline": bool(beats),
                }

    json_path = os.path.join(REPORT_DIR, "candidate_factor_matrix_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return df, summary


def generate_report(df, summary):
    s = summary

    beh = df[(df["period"] == "final_holdout") & (df["label"] == "baseline")]
    holdout_rows = []
    for _, r in beh.iterrows():
        holdout_rows.append(
            f"| {r['factor']} | {r['top_n']} | {r['weeks']} | "
            f"{r['excess_annual_return']*100:+.1f}% | {r['ir_vs_ew']:+.2f} | "
            f"{r['excess_win_rate']*100:.1f}% | {r['turnover']*100:.1f}% |"
        )

    vs_rows = []
    for key, v in s["best_candidate_vs_baseline"].items():
        sym = ">" if v["candidate_beats_baseline"] else "<="
        vs_rows.append(
            f"| {key} | {v['best_candidate_factor']} | {v['best_candidate_ir']:+.2f} | "
            f"{v['best_baseline_factor']} | {v['best_baseline_ir']:+.2f} | {sym} |"
        )

    report = f"""# candidate factor matrix

**Generated**: {s['generated_at']}
**GP**: {s['gp_status']}
**Phase 2**: {s['phase2_status']}

> Candidate factors are evaluated on train / validation / dev_test only.
> Final holdout is reported only for the frozen baseline.
> This does NOT approve Phase 2 or restart GP.

---

## 1. Setup

| Parameter | Value |
|-----------|-------|
| Universe | U3_volclose_mid60 (400 stocks) |
| Cost | turnover * 0.004 |
| Portfolios | Long-only Top50, Top100 |
| Dev periods | train (2023-2024), validation (2024-2025), dev_test (2025H2) |
| Final holdout | Frozen baseline only, not used for selection |

## 2. Candidate Factor Families

| Family | Factors |
|--------|---------|
| weekly_reversal | -ret_1w, -ret_4w, -ret_12w |
| weekly_volatility | -vol_4w, -vol_12w |
| weekly_activity | -volume, -amount, volume_z, amount_z |
| daily_derived | d_ret_5d, d_ret_20d, d_vol_20d, d_downside_vol_20d, d_range_20d, d_intraday_strength_5d, d_volume_z20, d_amount_z20 |

## 3. Candidate vs Baseline (best IR per period)

| Period+Portfolio | Best Candidate | Cand IR | Best Baseline | Base IR | Beats? |
|------------------|---------------|---------|---------------|---------|--------|
{chr(10).join(vs_rows)}

## 4. Frozen Baseline on Final Holdout (untouched)

| Factor | TopN | Weeks | Excess Ann | IR vs EW | Ex Win% | Turnover |
|--------|------|-------|------------|----------|---------|----------|
{chr(10).join(holdout_rows)}

## 5. Full Results

Parquet: `report/candidate_factor_matrix.parquet` ({len(df)} rows x {len(df.columns)} cols)

## 6. Status

| Item | Status |
|------|--------|
| GP | {s['gp_status']} |
| Phase 2 | {s['phase2_status']} |
| Candidates evaluated | {s['total_candidates']} |
| Baseline rows | {s['total_baseline_rows']} |

## 7. Generated Files

| File | Location |
|------|----------|
| Parquet | report/candidate_factor_matrix.parquet |
| Summary JSON | report/candidate_factor_matrix_summary.json |
| Report | report/candidate_factor_matrix.md |
| Report (analysis) | analysis/candidate_factor_matrix.md |
| Script | diagnostics/candidate_factor_matrix.py |
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        path = os.path.join(d, "candidate_factor_matrix.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)

    print(f"Reports written to {REPORT_DIR}/ and {ANALYSIS_DIR}/")


def main():
    df, summary = compute_all()
    generate_report(df, summary)

    beats_count = sum(1 for v in summary["best_candidate_vs_baseline"].values() if v["candidate_beats_baseline"])
    total = len(summary["best_candidate_vs_baseline"])
    print(f"Candidates: {summary['total_candidates']} rows")
    print(f"Baseline: {summary['total_baseline_rows']} rows")
    print(f"Beats baseline: {beats_count}/{total} period-portfolio combos")
    print(f"GP: {summary['gp_status']}, Phase 2: {summary['phase2_status']}")


if __name__ == "__main__":
    main()
