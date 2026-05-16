"""Model research readiness: feature audit and frozen baseline pack.

Reads data/weekly_daily_features.parquet, reports column coverage and
missingness by period, recomputes the frozen baseline pack.  Outputs
JSON and markdown reports.

This prepares model comparison.  It does NOT approve Phase 2, does NOT
restart GP, and does NOT tune on the final holdout period.

Period definitions (train-only universe construction uses train period):
  train:        2023-01-01 to 2024-06-30
  validation:   2024-07-01 to 2025-06-30
  dev_test:     2025-07-01 to 2025-12-31
  final_holdout: 2026-01-01+

Outputs:
  report/model_research_readiness.json
  report/model_research_readiness.md
  analysis/model_research_readiness.md
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
    compute_simple_factor,
    load_data,
    portfolio_metrics,
)

REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"
COST_RATE = 0.004
MAX_STOCKS = 400

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

PERIODS = {
    "train": ("2023-01-01", "2024-06-30"),
    "validation": ("2024-07-01", "2025-06-30"),
    "dev_test": ("2025-07-01", "2025-12-31"),
    "final_holdout": ("2026-01-01", None),
}

FROZEN_BASELINE = {
    "universe": "U3_volclose_mid60",
    "universe_train_start": "2023-01-01",
    "universe_train_end": "2025-12-31",
    "factors": ["-volume", "-ret_4w"],
    "portfolios": ["long_only_top50", "long_only_top100"],
    "benchmark": "universe_equal_weight",
    "cost_rate": COST_RATE,
    "cost_model": "turnover * cost_rate",
}


def build_u3_universe(weekly):
    t = weekly[(weekly["trade_date"] >= "2023-01-01") & (weekly["trade_date"] <= "2025-12-31")].copy()
    t["vc"] = t["volume"] * t["close"]
    vc = t.groupby("ts_code")["vc"].mean().sort_values(ascending=False)
    n = len(vc)
    lo = int(n * 0.20)
    hi = int(n * 0.80)
    mid = vc.iloc[lo:hi]
    if len(mid) > MAX_STOCKS:
        mid = mid.head(MAX_STOCKS)
    return mid.index.tolist()


def period_mask(dates, start, end):
    m = dates.astype(str) >= start
    if end is not None:
        m = m & (dates.astype(str) <= end)
    return m


def compute_all():
    weekly, _, _ = load_data()
    weekly["trade_date"] = pd.to_datetime(weekly["trade_date"])

    # ---- Feature audit ----
    cols = list(weekly.columns)
    feature_cols = [c for c in cols if c.startswith("d_")]
    ohlcv_cols = [c for c in ["open", "high", "low", "close", "volume", "amount"] if c in cols]

    missingness = {}
    for pname, (start, end) in PERIODS.items():
        m = period_mask(weekly["trade_date"], start, end)
        sub = weekly[m]
        total = len(sub)
        missingness[pname] = {
            "start": start,
            "end": end if end else "data_end",
            "total_rows": int(total),
            "unique_stocks": int(sub["ts_code"].nunique()),
            "weekly_dates": int(sub["trade_date"].nunique()),
        }
        for c in feature_cols:
            missingness[pname][f"{c}_pct_present"] = round(float(sub[c].notna().mean()), 4)

    # ---- Frozen baseline pack ----
    universe = build_u3_universe(weekly)
    pivots = build_pivots(weekly, universe, ["close", "high", "low", "volume"])
    fwd_full = compute_fwd_ret(pivots["close"])

    baseline_results = []
    for factor_name in FROZEN_BASELINE["factors"]:
        factor = compute_simple_factor(pivots, factor_name)
        for pname, (start, end) in PERIODS.items():
            m = period_mask(factor.index, start, end)
            fp = factor[m]
            fwp = fwd_full[fwd_full.index.isin(fp.index)]
            if len(fp) < 5:
                continue

            for top_n in [50, 100]:
                pf = build_long_only_portfolio(fp, fwp, n_stocks=top_n, cost_rate=COST_RATE)
                if len(pf) < 3:
                    continue
                m_abs = portfolio_metrics(pf["net_ret"])
                ew = fwp.mean(axis=1)
                ci = pf.index.intersection(ew.index)
                strategy = pf["net_ret"][ci]
                benchmark = ew[ci]
                excess = strategy - benchmark
                m_abs = portfolio_metrics(strategy)
                m_exc = portfolio_metrics(excess)
                m_ew = portfolio_metrics(benchmark)

                baseline_results.append({
                    "period": pname,
                    "period_start": start,
                    "period_end": end if end else "data_end",
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
                })

    result = {
        "generated_at": datetime.now().isoformat(),
        "data_source": "data/weekly_daily_features.parquet",
        "total_rows": int(len(weekly)),
        "date_range": [str(weekly["trade_date"].min().date()), str(weekly["trade_date"].max().date())],
        "columns": cols,
        "feature_columns": feature_cols,
        "ohlcv_columns": ohlcv_cols,
        "period_definitions": {k: {"start": v[0], "end": v[1] if v[1] else "data_end"} for k, v in PERIODS.items()},
        "column_missingness_by_period": missingness,
        "frozen_baseline_config": FROZEN_BASELINE,
        "universe_stock_count": len(universe),
        "baseline_results": baseline_results,
        "gp_status": "paused",
        "phase2_status": "paused",
        "disclaimer": "This prepares model comparison. It does NOT approve Phase 2, does NOT restart GP, and does NOT tune on final_holdout.",
    }

    json_path = os.path.join(REPORT_DIR, "model_research_readiness.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def generate_report(result):
    r = result

    # Build baseline table rows
    baseline_rows = []
    for b in r["baseline_results"]:
        baseline_rows.append(
            f"| {b['period']} | {b['factor']} | {b['top_n']} | {b['weeks']} | "
            f"{b['abs_annual_return']*100:+.1f}% | {b['abs_sharpe']:+.2f} | "
            f"{b['univ_ew_annual_return']*100:+.1f}% | {b['excess_annual_return']*100:+.1f}% | "
            f"{b['ir_vs_ew']:+.2f} | {b['excess_win_rate']*100:.1f}% | {b['turnover']*100:.1f}% |"
        )

    # Build missingness rows
    miss_rows = []
    for pname in ["train", "validation", "dev_test", "final_holdout"]:
        m = r["column_missingness_by_period"][pname]
        miss_rows.append(
            f"| {pname} | {m['total_rows']} | {m['unique_stocks']} | {m['weekly_dates']} | "
            + " | ".join(f"{m.get(c+'_pct_present', 0)*100:.0f}%" for c in r["feature_columns"])
            + " |"
        )
    miss_header = "| Period | Rows | Stocks | Weeks | " + " | ".join(r["feature_columns"]) + " |"

    report = f"""# model research readiness

**Generated**: {r['generated_at']}
**GP**: {r['gp_status']}
**Phase 2**: {r['phase2_status']}

> This prepares model comparison. It does NOT approve Phase 2, does NOT
> restart GP, and does NOT tune on the final holdout period.

---

## 1. Data Summary

| Item | Value |
|------|-------|
| Source | {r['data_source']} |
| Total rows | {r['total_rows']:,} |
| Date range | {r['date_range'][0]} to {r['date_range'][1]} |
| Feature columns | {len(r['feature_columns'])} ({', '.join(r['feature_columns'])}) |

## 2. Period Definitions

| Period | Start | End | Role |
|--------|-------|-----|------|
| train | {r['period_definitions']['train']['start']} | {r['period_definitions']['train']['end']} | Universe + baseline dev |
| validation | {r['period_definitions']['validation']['start']} | {r['period_definitions']['validation']['end']} | Factor selection |
| dev_test | {r['period_definitions']['dev_test']['start']} | {r['period_definitions']['dev_test']['end']} | Development test |
| final_holdout | {r['period_definitions']['final_holdout']['start']} | {r['period_definitions']['final_holdout']['end']} | Frozen, untuned |

## 3. Column Coverage by Period

{miss_header}
{chr(10).join(miss_rows)}

## 4. Frozen Baseline Configuration

| Parameter | Value |
|-----------|-------|
| Universe | {r['frozen_baseline_config']['universe']} |
| Universe train | {r['frozen_baseline_config']['universe_train_start']} to {r['frozen_baseline_config']['universe_train_end']} |
| Universe size | {r['universe_stock_count']} stocks |
| Factors | {', '.join(r['frozen_baseline_config']['factors'])} |
| Portfolios | {', '.join(r['frozen_baseline_config']['portfolios'])} |
| Benchmark | {r['frozen_baseline_config']['benchmark']} |
| Cost | {r['frozen_baseline_config']['cost_model']} |

## 5. Frozen Baseline Results (all periods)

| Period | Factor | TopN | Wks | Abs Ann | Abs Sharpe | EW Ann | Excess Ann | IR vs EW | Ex Win% | Turnover |
|--------|--------|------|-----|---------|-----------|--------|------------|----------|---------|----------|
{chr(10).join(baseline_rows)}

## 6. Status

| Item | Status |
|------|--------|
| GP | {r['gp_status']} |
| Phase 2 | {r['phase2_status']} |
| Final holdout tuning | Not performed |

## 7. Generated Files

| File | Location |
|------|----------|
| JSON metrics | report/model_research_readiness.json |
| Report | report/model_research_readiness.md |
| Report (analysis) | analysis/model_research_readiness.md |
| Script | diagnostics/model_research_readiness.py |
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        path = os.path.join(d, "model_research_readiness.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)

    print(f"Reports written to {REPORT_DIR}/ and {ANALYSIS_DIR}/")


def main():
    result = compute_all()
    generate_report(result)
    print(f"Universes: 1 ({result['universe_stock_count']} stocks)")
    print(f"Baseline results: {len(result['baseline_results'])} rows")
    print(f"GP: {result['gp_status']}, Phase 2: {result['phase2_status']}")


if __name__ == "__main__":
    main()
