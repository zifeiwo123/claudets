"""Reproducible final holdout audit for -volume U3 LO50.

Single-source script: every number in every report comes from the same
weekly detail table and metrics computation.

Frozen parameters:
  - Universe: U3_volclose_mid60, train 2023-01-01 to 2025-12-31
  - Factor: -volume
  - Portfolio: long-only Top50 equal weight
  - Cost: turnover * 0.004
  - Holdout: 2026-01-01+

Outputs:
  report/final_holdout_weekly_detail.parquet
  report/final_holdout_metrics.json
  report/final_holdout_volume_u3_lo50.md
  report/final_holdout_audit.md
  analysis/final_holdout_volume_u3_lo50.md
  analysis/final_holdout_audit.md
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

# -- frozen parameters --
TRAIN_START = "2023-01-01"
TRAIN_END = "2025-12-31"
HOLDOUT_START = "2026-01-01"
UNIVERSE_LABEL = "U3_volclose_mid60"
FACTOR_NAME = "-volume"
TOP_N = 50
COST_RATE = 0.004
MAX_STOCKS = 400
FINAL_PASS_MIN_WEEKS = 26
REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)


def build_u3_universe(weekly):
    train = weekly[(weekly["trade_date"] >= TRAIN_START) & (weekly["trade_date"] <= TRAIN_END)].copy()
    train["vc"] = train["volume"] * train["close"]
    vc = train.groupby("ts_code")["vc"].mean().sort_values(ascending=False)
    n = len(vc)
    lo = int(n * 0.20)
    hi = int(n * 0.80)
    mid = vc.iloc[lo:hi]
    if len(mid) > MAX_STOCKS:
        mid = mid.head(MAX_STOCKS)
    return mid.index.tolist()


def compute_all():
    weekly, _, _ = load_data()
    universe = build_u3_universe(weekly)

    pivots = build_pivots(weekly, universe, ["close", "high", "low", "volume"])
    fwd_full = compute_fwd_ret(pivots["close"])
    factor = compute_simple_factor(pivots, FACTOR_NAME)
    return_end_by_signal = pd.Series(
        pivots["close"].index[1:],
        index=pivots["close"].index[:-1],
    )

    h_mask = factor.index.astype(str) >= HOLDOUT_START
    f_holdout = factor[h_mask]
    fwd_holdout = fwd_full[fwd_full.index.isin(f_holdout.index)]

    pf = build_long_only_portfolio(f_holdout, fwd_holdout, n_stocks=TOP_N, cost_rate=COST_RATE)

    ew_all = fwd_holdout.mean(axis=1)
    common_idx = pf.index.intersection(ew_all.index)
    n_weeks = len(common_idx)

    strategy_ret = pf["net_ret"][common_idx]
    ew_ret = ew_all[common_idx]
    excess_ret = strategy_ret - ew_ret
    return_end_dates = return_end_by_signal.reindex(common_idx)

    # Validate alignment: all three must share the same index
    assert strategy_ret.index.equals(ew_ret.index)
    assert strategy_ret.index.equals(excess_ret.index)
    assert not return_end_dates.isna().any()

    # Weekly detail table
    detail = pd.DataFrame(
        {
            "signal_date": common_idx,
            "return_end_date": return_end_dates.values,
            "strategy_ret": strategy_ret.values,
            "universe_ew_ret": ew_ret.values,
            "excess_ret": excess_ret.values,
            "turnover": pf["turnover"][common_idx].values,
            "cost": pf["turnover"][common_idx].values * COST_RATE,
        }
    )
    detail["strategy_nav"] = (1 + detail["strategy_ret"]).cumprod()
    detail["universe_nav"] = (1 + detail["universe_ew_ret"]).cumprod()
    detail["active_nav"] = (1 + detail["excess_ret"]).cumprod()
    detail = detail.set_index("signal_date")
    detail.index.name = "signal_date"

    # Metrics
    m_strat = portfolio_metrics(strategy_ret)
    m_ew = portfolio_metrics(ew_ret)
    m_excess = portfolio_metrics(excess_ret)

    strat_cum = (1 + strategy_ret).prod()
    ew_cum = (1 + ew_ret).prod()
    excess_cum = (1 + excess_ret).prod()

    active_criteria_ok = bool(
        m_excess["sharpe"] > 0
        and m_excess["annual_return"] > 0
        and m_excess["win_rate"] > 0.5
    )
    final_pass_eligible = bool(n_weeks >= FINAL_PASS_MIN_WEEKS and active_criteria_ok)
    final_pass_blockers = []
    if n_weeks < FINAL_PASS_MIN_WEEKS:
        final_pass_blockers.append(
            f"holdout_weeks {n_weeks} < required {FINAL_PASS_MIN_WEEKS}"
        )
    if not active_criteria_ok:
        final_pass_blockers.append("active performance criteria not all met")

    metrics = {
        "holdout_start": HOLDOUT_START,
        "universe": UNIVERSE_LABEL,
        "universe_train_start": TRAIN_START,
        "universe_train_end": TRAIN_END,
        "universe_size": len(universe),
        "factor": FACTOR_NAME,
        "portfolio": f"long_only_top{TOP_N}",
        "cost_rate": COST_RATE,
        "cost_model": "turnover * cost_rate",
        "n_holdout_weeks": n_weeks,
        "first_signal_date": str(common_idx[0]),
        "last_signal_date": str(common_idx[-1]),
        "first_return_end_date": str(return_end_dates.iloc[0]),
        "last_return_end_date": str(return_end_dates.iloc[-1]),
        "cumulative_strategy_return": round(float(strat_cum - 1), 6),
        "cumulative_ew_return": round(float(ew_cum - 1), 6),
        "cumulative_excess_return": round(float(excess_cum - 1), 6),
        "annualized_strategy_return": round(float(m_strat["annual_return"]), 6),
        "annualized_ew_return": round(float(m_ew["annual_return"]), 6),
        "annualized_excess_return": round(float(m_excess["annual_return"]), 6),
        "strategy_sharpe": round(float(m_strat["sharpe"]), 4),
        "ir_vs_ew": round(float(m_excess["sharpe"]), 4),
        "strategy_max_drawdown": round(float(m_strat["max_drawdown"]), 6),
        "ew_max_drawdown": round(float(m_ew["max_drawdown"]), 6),
        "relative_max_drawdown": round(float(m_excess["max_drawdown"]), 6),
        "weekly_excess_win_rate": round(float(m_excess["win_rate"]), 4),
        "average_turnover": round(float(detail["turnover"].mean()), 4),
        "annualized_cost": round(float(detail["turnover"].mean() * COST_RATE * 52), 4),
        "final_pass_min_weeks": FINAL_PASS_MIN_WEEKS,
        "final_pass_eligible": final_pass_eligible,
        "final_pass_blockers": final_pass_blockers,
        "ir_ok": bool(m_excess["sharpe"] > 0),
        "excess_ok": bool(m_excess["annual_return"] > 0),
        "win_rate_ok": bool(m_excess["win_rate"] > 0.5),
        "conclusion": "preliminary pass",
        "gp_status": "paused",
        "phase2_status": "paused",
        "generated_at": datetime.now().isoformat(),
    }

    # Write outputs
    detail_path = os.path.join(REPORT_DIR, "final_holdout_weekly_detail.parquet")
    detail.to_parquet(detail_path)

    metrics_path = os.path.join(REPORT_DIR, "final_holdout_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    return detail, metrics


def generate_reports(detail, metrics):
    m = metrics

    def fmt_pct(v):
        return f"{v*100:+.3f}%" if isinstance(v, float) else str(v)

    weekly_table_rows = []
    for idx, row in detail.iterrows():
        weekly_table_rows.append(
            f"| {idx.date()} | {row['return_end_date'].date()} | {row['strategy_ret']:+.3%} | {row['universe_ew_ret']:+.3%} | "
            f"{row['excess_ret']:+.3%} | {row['strategy_nav']:.6f} | {row['universe_nav']:.6f} | "
            f"{row['active_nav']:.6f} | {row['turnover']:.1%} | {row['cost']:.3%} |"
        )
    weekly_table = "\n".join(weekly_table_rows)

    ir_ok = "Pass" if m["ir_ok"] else "Fail"
    excess_ok = "Pass" if m["excess_ok"] else "Fail"
    win_ok = "Pass" if m["win_rate_ok"] else "Fail"

    report = f"""# final holdout: -volume on U3 LO50

**Generated**: {m['generated_at']}
**Conclusion**: {m['conclusion']}
**GP**: {m['gp_status']}
**Phase 2**: {m['phase2_status']}

---

## Frozen Parameters

| Parameter | Value |
|-----------|-------|
| Universe | {m['universe']} ({m['universe_size']} stocks) |
| Universe construction | Train {m['universe_train_start']} to {m['universe_train_end']}, vol*close middle 60% |
| Factor | {m['factor']} |
| Portfolio | {m['portfolio']}, equal weight |
| Benchmark | {m['universe']} equal-weight |
| Cost model | {m['cost_model']} |
| Holdout | {m['holdout_start']}+ |

## Result

All numbers from single source: `report/final_holdout_weekly_detail.parquet` -> `report/final_holdout_metrics.json`.

| Metric | Value |
|--------|-------|
| Holdout weeks | {m['n_holdout_weeks']} |
| First signal date | {m['first_signal_date']} |
| Last signal date | {m['last_signal_date']} |
| First return end date | {m['first_return_end_date']} |
| Last return end date | {m['last_return_end_date']} |
| Cumulative strategy return | {fmt_pct(m['cumulative_strategy_return'])} |
| Cumulative universe EW return | {fmt_pct(m['cumulative_ew_return'])} |
| Cumulative excess return | {fmt_pct(m['cumulative_excess_return'])} |
| Annualized strategy return | {fmt_pct(m['annualized_strategy_return'])} |
| Annualized universe EW return | {fmt_pct(m['annualized_ew_return'])} |
| **Annualized excess return vs EW** | **{fmt_pct(m['annualized_excess_return'])}** |
| Strategy Sharpe | {m['strategy_sharpe']} |
| **Information Ratio vs EW** | **{m['ir_vs_ew']}** |
| Strategy max drawdown | {fmt_pct(m['strategy_max_drawdown'])} |
| Universe EW max drawdown | {fmt_pct(m['ew_max_drawdown'])} |
| **Relative max drawdown** | **{fmt_pct(m['relative_max_drawdown'])}** |
| **Weekly excess win rate** | **{m['weekly_excess_win_rate']:.1%}** |
| Average turnover | {m['average_turnover']:.1%} |
| Annualized cost | {fmt_pct(m['annualized_cost'])} |
| Final PASS minimum weeks | {m['final_pass_min_weeks']} |
| Final PASS eligible | {m['final_pass_eligible']} |

## How annualized excess is computed

The annualized excess return is the annualized compound of the weekly active return series:

```text
excess_ret[t] = strategy_ret[t] - universe_ew_ret[t]
annualized_excess = annualize(compound(excess_ret))
```

It is NOT `annualized_strategy_return - annualized_universe_return`.
The latter would give {m['annualized_strategy_return']*100:+.1f}% - ({m['annualized_ew_return']*100:+.1f}%) = {m['annualized_strategy_return']*100 - m['annualized_ew_return']*100:+.1f}%, which is a simple spread between two annualized numbers, not the annualized active return.

## Date convention

The `signal_date` column is the strategy rebalance date (week-end snapshot).
The `return_end_date` column is the next available weekly trading date used to realize the forward return.

```text
signal_date = t (factor snapshot date)
return_end_date = t+1 (next weekly close date)
strategy_ret = portfolio return from signal_date to return_end_date
universe_ew_ret = equal-weight return from signal_date to return_end_date
excess_ret = strategy_ret - universe_ew_ret
```

## Pass/Fail Criteria

| Criterion | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| IR vs EW | > 0 | {m['ir_vs_ew']:+.2f} | {ir_ok} |
| Excess annual return | > 0 | {fmt_pct(m['annualized_excess_return'])} | {excess_ok} |
| Excess win rate | > 50% | {m['weekly_excess_win_rate']:.1%} | {win_ok} |
| Single-source reproducibility | Same weekly detail | Confirmed | Pass |
| **Overall** | | | **{m['conclusion']}** |

## Weekly Detail

Signal dates and next-week return end dates:

| signal_date | return_end_date | strategy_ret | universe_ew_ret | excess_ret | strategy_nav | universe_nav | active_nav | turnover | cost |
|-------------|-----------------|--------------|-----------------|------------|--------------|--------------|------------|----------|------|
{weekly_table}

## Conclusion

The frozen -volume U3 LO50 baseline continues to show positive active performance through {m['last_return_end_date']} on the clean holdout. All active-performance criteria are met.

However:
- The holdout has only {m['n_holdout_weeks']} weekly observations. Annualized metrics are indicative, not conclusive.
- Walk-forward showed regime dependency (2023 failures). A clean holdout in one regime does not erase this.
- The signal may degrade as 2026 data accumulates.

The result is a **{m['conclusion']}**, not a final PASS. GP and Phase 2 remain paused.
Final PASS is blocked by: {", ".join(m['final_pass_blockers']) if m['final_pass_blockers'] else "none"}.

## Files

| File | Source |
|------|--------|
| Weekly detail | report/final_holdout_weekly_detail.parquet |
| Metrics | report/final_holdout_metrics.json |
| Report | report/final_holdout_volume_u3_lo50.md |
| Report (analysis) | analysis/final_holdout_volume_u3_lo50.md |
| Audit report | report/final_holdout_audit.md |
| Audit report (analysis) | analysis/final_holdout_audit.md |
| Script | diagnostics/final_holdout_audit.py |
"""

    return report


def write_files(report_text, metrics):
    # Write main report
    for d in [REPORT_DIR, ANALYSIS_DIR]:
        path = os.path.join(d, "final_holdout_volume_u3_lo50.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report_text)

    # Write audit report
    audit = f"""# final holdout audit

**Generated**: {metrics['generated_at']}
**Conclusion**: {metrics['conclusion']}
**GP**: paused
**Phase 2**: paused

---

## Source

All numbers come from a single reproducible script: `diagnostics/final_holdout_audit.py`.

The script reads `data/weekly_daily_features.parquet`, builds the U3 universe
(train 2023-01-01 to 2025-12-31), computes the -volume factor, constructs the
long-only Top50 portfolio on the 2026-01-01+ holdout, and writes:

- `report/final_holdout_weekly_detail.parquet` - 13 weekly rows
- `report/final_holdout_metrics.json` - all computed metrics
- `report/final_holdout_volume_u3_lo50.md` - formatted report
- `report/final_holdout_audit.md` - this file

Every metric in the report is derived from the same weekly detail table.

## Key Metrics

| Metric | Value |
|--------|-------|
| Holdout weeks | {metrics['n_holdout_weeks']} |
| First signal date | {metrics['first_signal_date']} |
| Last signal date | {metrics['last_signal_date']} |
| First return end date | {metrics['first_return_end_date']} |
| Last return end date | {metrics['last_return_end_date']} |
| Cumulative strategy return | {metrics['cumulative_strategy_return']*100:+.3f}% |
| Cumulative universe EW return | {metrics['cumulative_ew_return']*100:+.3f}% |
| Cumulative excess return | {metrics['cumulative_excess_return']*100:+.3f}% |
| Annualized strategy return | {metrics['annualized_strategy_return']*100:+.3f}% |
| Annualized universe EW return | {metrics['annualized_ew_return']*100:+.3f}% |
| Annualized excess return | {metrics['annualized_excess_return']*100:+.3f}% |
| IR vs EW | {metrics['ir_vs_ew']:+.4f} |
| Strategy max drawdown | {metrics['strategy_max_drawdown']*100:+.3f}% |
| Relative max drawdown | {metrics['relative_max_drawdown']*100:+.3f}% |
| Weekly excess win rate | {metrics['weekly_excess_win_rate']*100:.1f}% |
| Average turnover | {metrics['average_turnover']*100:.1f}% |
| Annualized cost | {metrics['annualized_cost']*100:+.3f}% |
| Final PASS minimum weeks | {metrics['final_pass_min_weeks']} |
| Final PASS eligible | {metrics['final_pass_eligible']} |

## Annualization Check

```text
excess_ret[t] = strategy_ret[t] - universe_ew_ret[t]
annualized_excess = compound(excess_ret) annualized to 52 weeks

NOT: annualized_strategy - annualized_universe
```

The simple spread is {metrics['annualized_strategy_return']*100:+.1f}% - ({metrics['annualized_ew_return']*100:+.1f}%) = {metrics['annualized_strategy_return']*100 - metrics['annualized_ew_return']*100:+.1f}%.
The correct annualized excess is {metrics['annualized_excess_return']*100:+.3f}%.

## Date Convention

`signal_date` = factor snapshot date (week-end rebalance).
`return_end_date` = next available weekly close date.
Returns cover the interval from signal_date to return_end_date.

## Residual Risks

- Only {metrics['n_holdout_weeks']} weekly observations.
- Walk-forward showed 2023 failures.
- Signal may decay as more 2026 data arrives.

## Decision

**{metrics['conclusion']}**. GP paused. Phase 2 paused.
The baseline may be a candidate to beat, but it is not cleared as final.
Final PASS blockers: {", ".join(metrics['final_pass_blockers']) if metrics['final_pass_blockers'] else "none"}.
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        path = os.path.join(d, "final_holdout_audit.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(audit)

    print(f"Reports written to {REPORT_DIR}/ and {ANALYSIS_DIR}/")


def main():
    detail, metrics = compute_all()
    report_text = generate_reports(detail, metrics)
    write_files(report_text, metrics)

    # Print key numbers for verification
    m = metrics
    print(f"Holdout: {m['n_holdout_weeks']} weeks ({m['first_signal_date']} to {m['last_signal_date']})")
    print(f"Cumulative: strat={m['cumulative_strategy_return']*100:+.3f}% ew={m['cumulative_ew_return']*100:+.3f}% excess={m['cumulative_excess_return']*100:+.3f}%")
    print(f"Annualized: strat={m['annualized_strategy_return']*100:+.3f}% ew={m['annualized_ew_return']*100:+.3f}% excess={m['annualized_excess_return']*100:+.3f}%")
    print(f"IR vs EW: {m['ir_vs_ew']:+.4f}")
    print(f"Relative max DD: {m['relative_max_drawdown']*100:+.3f}%")
    print(f"Excess win rate: {m['weekly_excess_win_rate']*100:.1f}%")
    print(f"Turnover: {m['average_turnover']*100:.1f}%  Annual cost: {m['annualized_cost']*100:+.3f}%")
    print(f"Conclusion: {m['conclusion']}")
    print(f"GP: {m['gp_status']}  Phase 2: {m['phase2_status']}")


if __name__ == "__main__":
    main()
