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

    # Active performance checks
    if not m.get("ir_ok"):
        errors.append(f"ir_vs_ew <= 0 ({m.get('ir_vs_ew', 'N/A')})")
    if not m.get("excess_ok"):
        errors.append(f"annualized_excess_return <= 0 ({m.get('annualized_excess_return', 'N/A')})")
    if not m.get("win_rate_ok"):
        errors.append(f"weekly_excess_win_rate <= 0.5 ({m.get('weekly_excess_win_rate', 'N/A')})")

    # Status checks
    if m.get("conclusion") != "preliminary pass":
        errors.append(f"conclusion is '{m.get('conclusion')}', expected 'preliminary pass'")
    if m.get("gp_status") != "paused":
        errors.append(f"gp_status is '{m.get('gp_status')}', expected 'paused'")
    if m.get("phase2_status") != "paused":
        errors.append(f"phase2_status is '{m.get('phase2_status')}', expected 'paused'")

    # Consistency: ir_ok must match ir_vs_ew > 0
    ir_val = m.get("ir_vs_ew", 0)
    if m.get("ir_ok") and ir_val <= 0:
        errors.append(f"ir_ok=True but ir_vs_ew={ir_val}")

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
