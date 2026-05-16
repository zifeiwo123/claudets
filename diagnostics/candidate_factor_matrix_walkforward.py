"""Walk-forward universe robustness check for candidate factors.

This script is a gate before any light_model_scout run.  It rebuilds the
U3 universe independently for each walk-forward window using only that
window's train period, then evaluates the candidate factor matrix on the
following validation period.

It does NOT use final_holdout for candidate selection, does NOT restart GP,
and does NOT approve Phase 2.

Outputs:
  report/candidate_factor_matrix_walkforward.parquet
  report/candidate_factor_matrix_walkforward_summary.json
  report/candidate_factor_matrix_walkforward.md
  analysis/candidate_factor_matrix_walkforward.md
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from diagnostics.candidate_factor_matrix import (
    BASELINE_FACTORS,
    CANDIDATE_FACTORS,
    COST_RATE,
    MAX_STOCKS,
    RAW_ACTIVITY_FACTORS,
    compute_weekly_factor,
)
from diagnostics.followup_diagnosis import (
    build_long_only_portfolio,
    build_pivots,
    compute_fwd_ret,
    load_data,
    portfolio_metrics,
)

REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

WALK_FORWARD_WINDOWS = [
    ("WF1_2023H1_to_2023H2", "2023-01-01", "2023-06-30", "2023-07-01", "2023-12-31"),
    ("WF2_2023_to_2024H1", "2023-01-01", "2023-12-31", "2024-01-01", "2024-06-30"),
    ("WF3_2023_2024H1_to_2024H2", "2023-01-01", "2024-06-30", "2024-07-01", "2024-12-31"),
    ("WF4_2023_2024_to_2025H1", "2023-01-01", "2024-12-31", "2025-01-01", "2025-06-30"),
    ("WF5_2023_2025H1_to_2025H2", "2023-01-01", "2025-06-30", "2025-07-01", "2025-12-31"),
]
TOP_NS = [50, 100]
DAILY_FIELDS = [
    "d_ret_5d",
    "d_ret_20d",
    "d_vol_20d",
    "d_downside_vol_20d",
    "d_range_20d",
    "d_intraday_strength_5d",
    "d_volume_z20",
    "d_amount_z20",
]


def build_u3_universe(weekly, train_start, train_end):
    train = weekly[(weekly["trade_date"] >= train_start) & (weekly["trade_date"] <= train_end)].copy()
    train["vc"] = train["volume"] * train["close"]
    vc = train.groupby("ts_code")["vc"].mean().sort_values(ascending=False)
    n = len(vc)
    lo, hi = int(n * 0.20), int(n * 0.80)
    mid = vc.iloc[lo:hi]
    if len(mid) > MAX_STOCKS:
        mid = mid.head(MAX_STOCKS)
    return mid.index.tolist()


def period_mask(dates, start, end):
    mask = dates.astype(str) >= start
    if end is not None:
        mask = mask & (dates.astype(str) <= end)
    return mask


def factor_category(name):
    if name in BASELINE_FACTORS:
        return "baseline"
    if name in RAW_ACTIVITY_FACTORS:
        return "raw_activity"
    if name.startswith("d_"):
        return "daily_derived"
    return "other_weekly"


def evaluate(factor, fwd, window_name, val_start, val_end, factor_name, top_n, category):
    fp = factor[period_mask(factor.index, val_start, val_end)]
    fwp = fwd[fwd.index.isin(fp.index)]
    if len(fp) < 5:
        return None

    pf = build_long_only_portfolio(fp, fwp, n_stocks=top_n, cost_rate=COST_RATE)
    if len(pf) < 3:
        return None

    ew = fwp.mean(axis=1)
    ci = pf.index.intersection(ew.index)
    strategy = pf["net_ret"][ci]
    benchmark = ew[ci]
    excess = strategy - benchmark

    m_abs = portfolio_metrics(strategy)
    m_ew = portfolio_metrics(benchmark)
    m_exc = portfolio_metrics(excess)

    return {
        "window": window_name,
        "val_start": val_start,
        "val_end": val_end,
        "factor": factor_name,
        "category": category,
        "top_n": int(top_n),
        "weeks": int(len(strategy)),
        "abs_annual_return": float(round(m_abs["annual_return"], 6)),
        "abs_sharpe": float(round(m_abs["sharpe"], 4)),
        "univ_ew_annual_return": float(round(m_ew["annual_return"], 6)),
        "excess_annual_return": float(round(m_exc["annual_return"], 6)),
        "ir_vs_ew": float(round(m_exc["sharpe"], 4)),
        "excess_win_rate": float(round(m_exc["win_rate"], 4)),
        "excess_max_drawdown": float(round(m_exc["max_drawdown"], 6)),
        "turnover": float(round(pf["turnover"].mean(), 4)),
        "annualized_cost": float(round(pf["turnover"].mean() * COST_RATE * 52, 4)),
    }


def compute_all():
    weekly, _, _ = load_data()
    rows = []

    for wf_name, train_start, train_end, val_start, val_end in WALK_FORWARD_WINDOWS:
        universe = build_u3_universe(weekly, train_start, train_end)
        wpivots = build_pivots(weekly, universe, ["close", "high", "low", "volume", "amount"])
        fwd = compute_fwd_ret(wpivots["close"])

        daily_pivots = {}
        w = weekly[weekly["ts_code"].isin(universe)].copy()
        for field in DAILY_FIELDS:
            if field in w.columns:
                daily_pivots[field] = w.pivot_table(
                    index="trade_date", columns="ts_code", values=field, aggfunc="last"
                ).sort_index()

        all_factor_frames = {}
        for factors in CANDIDATE_FACTORS.values():
            for factor_name in factors:
                all_factor_frames[factor_name] = compute_weekly_factor(wpivots, factor_name)
        for field, frame in daily_pivots.items():
            all_factor_frames[field] = frame

        for factor_name, frame in all_factor_frames.items():
            category = factor_category(factor_name)
            for top_n in TOP_NS:
                row = evaluate(frame, fwd, wf_name, val_start, val_end, factor_name, top_n, category)
                if row is not None:
                    row.update({
                        "train_start": train_start,
                        "train_end": train_end,
                        "universe": "U3_volclose_mid60_train_only",
                        "universe_size": len(universe),
                    })
                    rows.append(row)

    df = pd.DataFrame(rows)
    if len(df) == 0:
        raise RuntimeError("walk-forward candidate matrix produced no rows")

    # Compare each candidate to the best baseline IR in the same window/top_n.
    df["metric_gate"] = (
        (df["ir_vs_ew"] > 0)
        & (df["excess_annual_return"] > 0)
        & (df["excess_win_rate"] > 0.5)
    )
    df["best_baseline_ir"] = pd.NA
    df["beats_baseline_ir"] = False
    for (window, top_n), sub in df.groupby(["window", "top_n"]):
        base = sub[sub["category"] == "baseline"]
        if len(base) == 0:
            continue
        best_ir = float(base["ir_vs_ew"].max())
        idx = (df["window"] == window) & (df["top_n"] == top_n)
        df.loc[idx, "best_baseline_ir"] = best_ir
        df.loc[idx, "beats_baseline_ir"] = df.loc[idx, "ir_vs_ew"] > best_ir

    df["window_pass"] = df["metric_gate"] & df["beats_baseline_ir"]
    df.to_parquet(os.path.join(REPORT_DIR, "candidate_factor_matrix_walkforward.parquet"))

    grouped = []
    for (factor, top_n, category), sub in df.groupby(["factor", "top_n", "category"]):
        pass_count = int(sub["window_pass"].sum())
        grouped.append({
            "factor": factor,
            "top_n": int(top_n),
            "category": category,
            "windows": int(sub["window"].nunique()),
            "pass_count": pass_count,
            "mean_ir": float(round(sub["ir_vs_ew"].mean(), 4)),
            "mean_excess_annual_return": float(round(sub["excess_annual_return"].mean(), 6)),
            "mean_turnover": float(round(sub["turnover"].mean(), 4)),
            "survives_walk_forward": bool(
                category not in {"baseline", "raw_activity"} and pass_count >= 3
            ),
        })

    grouped = sorted(grouped, key=lambda r: (r["survives_walk_forward"], r["pass_count"], r["mean_ir"]), reverse=True)
    survivors = [r for r in grouped if r["survives_walk_forward"]]
    summary = {
        "generated_at": datetime.now().isoformat(),
        "rows": int(len(df)),
        "windows": len(WALK_FORWARD_WINDOWS),
        "universe": "U3_volclose_mid60 rebuilt per window from train-only data",
        "final_holdout_used": False,
        "surviving_new_candidates": survivors,
        "model_scout_gate": (
            "walk_forward_pass_but_human_approval_required"
            if survivors
            else "blocked_no_candidate_survived_walk_forward"
        ),
        "gp_status": "paused",
        "phase2_status": "paused",
    }
    with open(os.path.join(REPORT_DIR, "candidate_factor_matrix_walkforward_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return df, grouped, summary


def generate_report(df, grouped, summary):
    top_rows = grouped[:20]
    top_table = "\n".join(
        f"| {r['category']} | {r['factor']} | {r['top_n']} | "
        f"{r['pass_count']}/{r['windows']} | {r['mean_ir']:+.2f} | "
        f"{r['mean_excess_annual_return']*100:+.1f}% | {r['mean_turnover']*100:.1f}% | "
        f"{'Y' if r['survives_walk_forward'] else 'N'} |"
        for r in top_rows
    )
    survivor_lines = (
        "\n".join(f"- {r['factor']} LO{r['top_n']}: {r['pass_count']}/{r['windows']} windows" for r in summary["surviving_new_candidates"])
        if summary["surviving_new_candidates"]
        else "No non-baseline, non-raw-activity candidate passes at least 3 of 5 windows."
    )

    report = f"""# candidate factor matrix walk-forward universe check

**Generated**: {summary['generated_at']}
**GP**: {summary['gp_status']}
**Phase 2**: {summary['phase2_status']}

> This is a pre-model-scout gate.  Each window rebuilds the U3 universe from
> train-only data, evaluates candidates on the following validation period,
> and never uses final_holdout for candidate selection.

---

## 1. Gate Result

| Gate | Status |
|------|--------|
| Final holdout used | {summary['final_holdout_used']} |
| Universe | {summary['universe']} |
| light_model_scout | {summary['model_scout_gate']} |

## 2. Surviving New Candidates

{survivor_lines}

Survival rule: non-baseline, non-raw-activity candidate must pass at least
3 of 5 windows.  A window pass requires IR vs EW > 0, positive annualized
excess return, excess win rate > 50%, and IR above the best frozen baseline
for the same window and TopN.

## 3. Top Walk-forward Rows

| Category | Factor | TopN | Passes | Mean IR | Mean Excess Ann | Mean Turnover | Survives? |
|----------|--------|------|--------|---------|-----------------|---------------|-----------|
{top_table}

## 4. Governance

- This check does not approve Phase 2.
- This check does not restart GP.
- If a candidate survives, a human still needs to approve any bounded
  `diagnostics/light_model_scout.py` run.
- Raw activity candidates remain blocked pending exposure review.

## 5. Generated Files

| File | Location |
|------|----------|
| Parquet | report/candidate_factor_matrix_walkforward.parquet |
| Summary JSON | report/candidate_factor_matrix_walkforward_summary.json |
| Report | report/candidate_factor_matrix_walkforward.md |
| Report (analysis) | analysis/candidate_factor_matrix_walkforward.md |
| Script | diagnostics/candidate_factor_matrix_walkforward.py |
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        with open(os.path.join(d, "candidate_factor_matrix_walkforward.md"), "w", encoding="utf-8") as f:
            f.write(report)


def main():
    df, grouped, summary = compute_all()
    generate_report(df, grouped, summary)
    print(f"Rows: {len(df)}")
    print(f"Surviving new candidates: {len(summary['surviving_new_candidates'])}")
    print(f"light_model_scout: {summary['model_scout_gate']}")
    print(f"GP: {summary['gp_status']}, Phase 2: {summary['phase2_status']}")


if __name__ == "__main__":
    main()
