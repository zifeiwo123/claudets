"""Lightweight integrity check for final holdout outputs.

This script loads `report/final_holdout_metrics.json` and verifies
the holdout status is consistent. It does NOT recompute anything.

Exit code 0: consistent.
Exit code 1: inconsistency found (preliminary pass broken).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

METRICS_PATH = Path("report/final_holdout_metrics.json")

REQUIRED_KEYS = [
    "n_holdout_weeks",
    "first_signal_date",
    "last_signal_date",
    "first_return_end_date",
    "last_return_end_date",
    "cumulative_strategy_return",
    "cumulative_ew_return",
    "cumulative_excess_return",
    "annualized_strategy_return",
    "annualized_ew_return",
    "annualized_excess_return",
    "ir_vs_ew",
    "strategy_max_drawdown",
    "ew_max_drawdown",
    "relative_max_drawdown",
    "weekly_excess_win_rate",
    "average_turnover",
    "annualized_cost",
    "ir_ok",
    "excess_ok",
    "win_rate_ok",
    "conclusion",
    "gp_status",
    "phase2_status",
]


def check():
    errors = []

    if not METRICS_PATH.exists():
        print(f"FAIL: {METRICS_PATH} not found. Run diagnostics/final_holdout_audit.py first.")
        sys.exit(1)

    try:
        with open(METRICS_PATH, encoding="utf-8") as f:
            m = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: cannot read {METRICS_PATH}: {exc}")
        sys.exit(1)

    # Required keys
    for key in REQUIRED_KEYS:
        if key not in m:
            errors.append(f"missing key: {key}")

    ir_val = m.get("ir_vs_ew")
    excess_ann = m.get("annualized_excess_return")
    excess_cum = m.get("cumulative_excess_return")
    win_rate = m.get("weekly_excess_win_rate")

    # Active performance checks use raw numeric values, not only the boolean flags.
    if not isinstance(ir_val, (int, float)) or ir_val <= 0:
        errors.append(f"ir_vs_ew <= 0 ({ir_val if ir_val is not None else 'N/A'})")
    if not isinstance(excess_ann, (int, float)) or excess_ann <= 0:
        errors.append(
            f"annualized_excess_return <= 0 ({excess_ann if excess_ann is not None else 'N/A'})"
        )
    if not isinstance(excess_cum, (int, float)) or excess_cum <= 0:
        errors.append(
            f"cumulative_excess_return <= 0 ({excess_cum if excess_cum is not None else 'N/A'})"
        )
    if not isinstance(win_rate, (int, float)) or win_rate <= 0.5:
        errors.append(f"weekly_excess_win_rate <= 0.5 ({win_rate if win_rate is not None else 'N/A'})")

    # Status checks
    if m.get("conclusion") != "preliminary pass":
        errors.append(f"conclusion is '{m.get('conclusion')}', expected 'preliminary pass'")
    if m.get("gp_status") != "paused":
        errors.append(f"gp_status is '{m.get('gp_status')}', expected 'paused'")
    if m.get("phase2_status") != "paused":
        errors.append(f"phase2_status is '{m.get('phase2_status')}', expected 'paused'")

    # Consistency: status flags must match numeric values.
    if m.get("ir_ok") != (isinstance(ir_val, (int, float)) and ir_val > 0):
        errors.append(f"ir_ok={m.get('ir_ok')} inconsistent with ir_vs_ew={ir_val}")
    if m.get("excess_ok") != (isinstance(excess_ann, (int, float)) and excess_ann > 0):
        errors.append(
            f"excess_ok={m.get('excess_ok')} inconsistent with annualized_excess_return={excess_ann}"
        )
    if m.get("win_rate_ok") != (isinstance(win_rate, (int, float)) and win_rate > 0.5):
        errors.append(
            f"win_rate_ok={m.get('win_rate_ok')} inconsistent with weekly_excess_win_rate={win_rate}"
        )

    # Sanity: weeks should be positive
    if m.get("n_holdout_weeks", 0) <= 0:
        errors.append(f"n_holdout_weeks={m.get('n_holdout_weeks')} is non-positive")

    # Sanity: turnover in reasonable range
    to = m.get("average_turnover", 0)
    if not (0 < to < 1.5):
        errors.append(f"average_turnover={to} out of (0, 1.5) range")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("OK: final holdout status is consistent")
    print(f"  weeks: {m['n_holdout_weeks']}")
    print(f"  IR vs EW: {m['ir_vs_ew']:+.4f}")
    print(f"  excess ann: {m['annualized_excess_return']*100:+.3f}%")
    print(f"  excess win rate: {m['weekly_excess_win_rate']*100:.1f}%")
    print(f"  conclusion: {m['conclusion']}")
    print(f"  gp: {m['gp_status']}, phase2: {m['phase2_status']}")


if __name__ == "__main__":
    check()
