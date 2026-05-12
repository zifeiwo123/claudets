#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stop hook that asks for a delivery summary after edits."""
import json
import os
import sys
from pathlib import Path

try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}

cwd = Path(payload.get("cwd") or os.getcwd())
state_dir = cwd / ".claude" / "state"
needs = state_dir / "needs_closing_review.txt"
prompted = state_dir / "closing_review_prompted.txt"

if needs.exists() and not prompted.exists():
    try:
        changed = needs.read_text(encoding="utf-8", errors="ignore").strip()
        prompted.write_text("prompted", encoding="utf-8")
    except Exception:
        changed = ""
    print(
        "[claudets Stop blocked]\n"
        "Files changed in this turn. Before closing, provide:\n"
        "1. changed files;\n"
        "2. why they changed;\n"
        "3. syntax checks or tests run;\n"
        "4. whether backtest/report must be rerun;\n"
        "5. remaining risks and next steps.\n\n"
        f"Changed files:\n{changed}",
        file=sys.stderr,
    )
    sys.exit(2)

try:
    if needs.exists():
        needs.unlink()
    if prompted.exists():
        prompted.unlink()
except Exception:
    pass

sys.exit(0)
