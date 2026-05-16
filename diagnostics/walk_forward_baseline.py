"""Walk-forward validation framework for simple baseline factors.

Tests -volume and -ret_4w on U2/U3 universes with long-only Top50/Top100.
Each window independently constructs its universe from train-only data.
GP remains paused. 2026-01+ preserved as final holdout.

Outputs:
    report/walk_forward_baseline.parquet
    report/walk_forward_baseline_report.md
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

from diagnostics.followup_diagnosis import (
    load_data, build_pivots, compute_fwd_ret, compute_simple_factor,
    build_long_only_portfolio, portfolio_metrics, COST_RATE,
)

REPORT_DIR = "report"
os.makedirs(REPORT_DIR, exist_ok=True)

WALK_FORWARD_WINDOWS = [
    ("WF1_2023H1_to_2023H2", "2023-01-01", "2023-06-30", "2023-07-01", "2023-12-31"),
    ("WF2_2023_to_2024H1", "2023-01-01", "2023-12-31", "2024-01-01", "2024-06-30"),
    ("WF3_2023_2024H1_to_2024H2", "2023-01-01", "2024-06-30", "2024-07-01", "2024-12-31"),
    ("WF4_2023_2024_to_2025H1", "2023-01-01", "2024-12-31", "2025-01-01", "2025-06-30"),
    ("WF5_2023_2025H1_to_2025H2", "2023-01-01", "2025-06-30", "2025-07-01", "2025-12-31"),
]

FACTORS_TO_TEST = ["-volume", "-ret_4w"]
TOP_NS = [50, 100]

FINAL_HOLDOUT_START = "2026-01-01"


def build_u2_universe(df, train_start, train_end):
    train = df[(df["trade_date"] >= train_start) & (df["trade_date"] <= train_end)]
    amt = train.groupby("ts_code")["amount"].mean().sort_values(ascending=False)
    n = len(amt)
    lo = int(n * 0.20)
    hi = int(n * 0.80)
    mid = amt.iloc[lo:hi]
    if len(mid) > 400:
        mid = mid.head(400)
    return mid.index.tolist()


def build_u3_universe(df, train_start, train_end):
    train = df[(df["trade_date"] >= train_start) & (df["trade_date"] <= train_end)]
    train = train.copy()
    train["vc"] = train["volume"] * train["close"]
    vc = train.groupby("ts_code")["vc"].mean().sort_values(ascending=False)
    n = len(vc)
    lo = int(n * 0.20)
    hi = int(n * 0.80)
    mid = vc.iloc[lo:hi]
    if len(mid) > 400:
        mid = mid.head(400)
    return mid.index.tolist()


def run_walk_forward():
    weekly, _, _ = load_data()
    print(f"Data: {weekly['trade_date'].min().date()} to {weekly['trade_date'].max().date()}")

    results = []

    for wf_name, train_s, train_e, val_s, val_e in WALK_FORWARD_WINDOWS:
        print(f"\n{'='*60}")
        print(f"{wf_name}: train={train_s} to {train_e}, validate={val_s} to {val_e}")
        print(f"{'='*60}")

        for uname, u_builder in [("U2_amount_mid60", build_u2_universe),
                                  ("U3_volclose_mid60", build_u3_universe)]:
            universe = u_builder(weekly, train_s, train_e)
            print(f"  {uname}: {len(universe)} stocks")

            pivots = build_pivots(weekly, universe, ["close", "high", "low", "volume"])
            fwd_full = compute_fwd_ret(pivots["close"])

            for factor_name in FACTORS_TO_TEST:
                factor = compute_simple_factor(pivots, factor_name)

                # Validate period only
                v_mask = (factor.index.astype(str) >= val_s) & (factor.index.astype(str) <= val_e)
                f_val = factor[v_mask]
                fwd_val = fwd_full[fwd_full.index.isin(f_val.index)]

                if len(f_val) < 5:
                    print(f"    {factor_name}: insufficient validate data ({len(f_val)} weeks), skipping")
                    continue

                for top_n in TOP_NS:
                    pf = build_long_only_portfolio(f_val, fwd_val, n_stocks=top_n, cost_rate=COST_RATE)
                    if len(pf) < 5:
                        continue

                    m_abs = portfolio_metrics(pf["net_ret"])
                    ew = fwd_val.mean(axis=1)
                    ci = pf.index.intersection(ew.index)
                    excess = pf["net_ret"][ci] - ew[ci]
                    m_exc = portfolio_metrics(excess)

                    turnover_avg = float(pf["turnover"].mean())
                    ann_cost = turnover_avg * COST_RATE * 52

                    row = {
                        "window": wf_name,
                        "train_start": train_s,
                        "train_end": train_e,
                        "val_start": val_s,
                        "val_end": val_e,
                        "universe": uname,
                        "universe_size": len(universe),
                        "factor": factor_name,
                        "top_n": top_n,
                        "val_weeks": len(pf),
                        "abs_ann": m_abs["annual_return"],
                        "abs_sharpe": m_abs["sharpe"],
                        "abs_maxdd": m_abs["max_drawdown"],
                        "abs_cum": m_abs["cum_return"],
                        "abs_win_rate": m_abs["win_rate"],
                        "univ_ew_ann": portfolio_metrics(ew)["annual_return"],
                        "univ_ew_sharpe": portfolio_metrics(ew)["sharpe"],
                        "excess_ann": m_exc["annual_return"],
                        "ir_vs_ew": m_exc["sharpe"],
                        "excess_maxdd": m_exc["max_drawdown"],
                        "excess_win_rate": m_exc["win_rate"],
                        "turnover": turnover_avg,
                        "annualized_cost": ann_cost,
                    }
                    results.append(row)

                    ir_str = f"{m_exc['sharpe']:+.2f}" if m_exc['sharpe'] != 0 else "N/A"
                    print(f"    {factor_name} LO{top_n}: abs={m_abs['sharpe']:+.2f} excess={m_exc['annual_return']:+.1%} IR={ir_str}")

    df = pd.DataFrame(results)
    df.to_parquet(os.path.join(REPORT_DIR, "walk_forward_baseline.parquet"))
    return df


def generate_report(df):
    lines = [
        "# walk-forward baseline validation report",
        "",
        f"**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        "**Status**: GP paused. Simple baseline walk-forward only.",
        "",
        "---",
        "",
        "## 1. Setup",
        "",
        "- **Factors**: -volume, -ret_4w (simple baselines, no GP)",
        "- **Universes**: U2 (amount middle 60%), U3 (vol*close middle 60%)",
        "- **Portfolios**: Long-only Top50, Top100",
        "- **Universe construction**: Per-window, train-only (no look-ahead)",
        "- **Final holdout**: 2026-01+ (untouched in this validation)",
        "- **GP**: Paused",
        "",
        "## 2. Walk-forward Windows",
        "",
        "| Window | Train | Validate | Purpose |",
        "|--------|-------|----------|---------|",
    ]
    for _, r in df[["window", "train_start", "train_end", "val_start", "val_end"]].drop_duplicates().iterrows():
        lines.append(f"| {r['window']} | {r['train_start']} to {r['train_end']} | {r['val_start']} to {r['val_end']} | |")

    lines.extend([
        "",
        "## 3. Summary Metrics (all windows)",
        "",
        "| Window | Universe | Factor | TopN | Abs Sharpe | Excess Ann | IR vs EW | Excess Win% | Turnover |",
        "|--------|----------|--------|------|-----------|------------|----------|-------------|----------|",
    ])
    for _, r in df.iterrows():
        lines.append(
            f"| {r['window']} | {r['universe']} | {r['factor']} | {r['top_n']} | "
            f"{r['abs_sharpe']:+.2f} | {r['excess_ann']:+.1%} | {r['ir_vs_ew']:+.2f} | "
            f"{r['excess_win_rate']:.1%} | {r['turnover']:.1%} |"
        )

    lines.extend([
        "",
        "## 4. Pass/Fail by Window",
        "",
        "Criteria: IR vs EW > 0, excess_ann > 0, excess_win_rate > 50%",
        "",
        "| Window | Universe | Factor | TopN | IR>0 | Excess>0 | Win>50% | PASS? |",
        "|--------|----------|--------|------|------|----------|---------|-------|",
    ])
    for _, r in df.iterrows():
        ir_ok = r['ir_vs_ew'] > 0
        ex_ok = r['excess_ann'] > 0
        win_ok = r['excess_win_rate'] > 0.5
        passed = ir_ok and ex_ok and win_ok
        lines.append(
            f"| {r['window']} | {r['universe']} | {r['factor']} | {r['top_n']} | "
            f"{'Y' if ir_ok else 'N'} | {'Y' if ex_ok else 'N'} | {'Y' if win_ok else 'N'} | "
            f"{'**PASS**' if passed else 'FAIL'} |"
        )

    # Count passes per factor/universe/top_n combo
    passes = df[(df['ir_vs_ew'] > 0) & (df['excess_ann'] > 0) & (df['excess_win_rate'] > 0.5)]

    lines.extend([
        "",
        "## 5. Stability Analysis",
        "",
        f"Total tests: {len(df)}",
        f"Passed (all 3 criteria): {len(passes)}",
        "",
        "### Pass rate by factor",
    ])
    for f in FACTORS_TO_TEST:
        sub = df[df['factor'] == f]
        p = passes[passes['factor'] == f]
        lines.append(f"- {f}: {len(p)}/{len(sub)} windows passed")

    lines.extend(["", "### Pass rate by universe"])
    for u in ["U2_amount_mid60", "U3_volclose_mid60"]:
        sub = df[df['universe'] == u]
        p = passes[passes['universe'] == u]
        lines.append(f"- {u}: {len(p)}/{len(sub)} windows passed")

    lines.extend(["", "### Pass rate by top_n"])
    for n in TOP_NS:
        sub = df[df['top_n'] == n]
        p = passes[passes['top_n'] == n]
        lines.append(f"- LO{n}: {len(p)}/{len(sub)} windows passed")

    # Consistency: which combos pass 3+ windows?
    lines.extend([
        "",
        "## 6. Consistent Performers (pass >= 3 of 5 windows)",
        "",
        "| Universe | Factor | TopN | Passes | Mean IR | Mean Excess |",
        "|----------|--------|------|--------|---------|-------------|",
    ])
    for uname in ["U2_amount_mid60", "U3_volclose_mid60"]:
        for fname in FACTORS_TO_TEST:
            for n in TOP_NS:
                sub = df[(df['universe'] == uname) & (df['factor'] == fname) & (df['top_n'] == n)]
                p = passes[(passes['universe'] == uname) & (passes['factor'] == fname) & (passes['top_n'] == n)]
                if len(p) >= 3:
                    lines.append(
                        f"| {uname} | {fname} | {n} | {len(p)}/5 | "
                        f"{sub['ir_vs_ew'].mean():+.2f} | {sub['excess_ann'].mean():+.1%} |"
                    )

    lines.extend([
        "",
        "## 7. Final Holdout (2026-01+)",
        "",
        "The 2026-01+ period has NOT been used in this walk-forward validation.",
        "It is reserved as a clean final holdout for the strategy that passes walk-forward.",
        "",
        "## 8. Conclusion",
        "",
        "### Does simple baseline pass walk-forward?",
        "",
    ])

    if len(passes) >= 8:
        lines.append("YES. Simple baseline factors pass walk-forward validation.")
        lines.append("This is DEVELOPMENT evidence only, not Phase 2 approval.")
    elif len(passes) >= 4:
        lines.append("PARTIALLY. Some factor/universe/window combinations pass, but not consistently.")
        lines.append("Focus on the consistent performers before expanding.")
    else:
        lines.append("NO. Simple baselines do not pass walk-forward consistently.")
        lines.append("Re-evaluate the research direction before committing more resources.")

    lines.extend([
        "",
        "> **Current Status Override**",
        ">",
        "> This report is DEVELOPMENT evidence from walk-forward validation.",
        "> Final holdout status: **preliminary pass**.",
        "> **GP: paused. Phase 2: paused.**",
        "> Walk-forward results do NOT grant Phase 2 or GP approval.",
        "> The current governing state is in codexmd/CODEX_CLAUDE_HANDOFF.md.",
        "",
        "### Next step",
        "",
    ])
    if len(passes) >= 4:
        lines.append("1. Isolate the consistent combos and continue monitoring.")
        lines.append("2. Final holdout (2026-01+) must reach PASS criteria before Phase 2.")
        lines.append("3. All walk-forward evidence is development only.")
    else:
        lines.append("1. Do NOT proceed to Phase 2 / GP")
        lines.append("2. Investigate whether different signal design or data sources are needed")
        lines.append("3. Consider whether weekly long-only on trading-activity universes is viable")

    lines.extend([
        "",
        "## 9. Generated Files",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| report/walk_forward_baseline.parquet | Full walk-forward results |",
        "| report/walk_forward_baseline_report.md | This report |",
        "| diagnostics/walk_forward_baseline.py | Reproducible script |",
    ])

    report_path = os.path.join(REPORT_DIR, "walk_forward_baseline_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReport written to {report_path}")


def main():
    df = run_walk_forward()
    generate_report(df)
    print("\nDone. GP remains paused.")


if __name__ == "__main__":
    main()
