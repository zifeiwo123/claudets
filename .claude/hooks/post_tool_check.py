#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PostToolUse checks for claudets edits."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print("[claudets PostToolUse check]\n" + msg, file=sys.stderr)
    sys.exit(2)


try:
    payload = json.load(sys.stdin)
except Exception as exc:
    fail(f"Cannot parse hook input: {exc}")

cwd = Path(payload.get("cwd") or os.getcwd())
tool_input = payload.get("tool_input", {}) or {}

paths = []
for key in ("file_path", "path"):
    if tool_input.get(key):
        p = Path(str(tool_input[key]))
        paths.append(p if p.is_absolute() else cwd / p)

scan_files = [
    p for p in paths
    if p.exists() and p.suffix.lower() in {".py", ".md", ".json", ".yaml", ".yml"}
]

patterns = [
    (
        re.compile(r"rets?_net\s*=\s*rets?_\w+\s*\*\s*\(\s*1\s*-", re.I),
        "Suspicious multiplicative cost deduction. Prefer raw_ret - turnover * cost_rate.",
    ),
    (
        re.compile(r"\.clip\s*\(\s*lower\s*=\s*-?0?\.\d+", re.I),
        "Suspicious post-hoc return clipping. Drawdown control must use only prior information.",
    ),
    (
        re.compile(r"dt\.start_time", re.I),
        "Weekly strategy dates should use the last real trading day, not period start_time.",
    ),
    (
        re.compile(r"TUSHARE_TOKEN\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]", re.I),
        "Hard-coded Tushare token detected. Use os.getenv('TUSHARE_TOKEN').",
    ),
    (
        re.compile(r"pool\.update_ic_results\(\{[^:]+:\s*ic_tr", re.I),
        "Factor pool appears to store train IC. Store validation IC for selection and direction.",
    ),
    (
        re.compile(r"direction\s*=\s*1\s+if\s+ic\.get\('ic_mean'", re.I),
        "Signal direction may be inferred from generic IC. Prefer stored validation direction.",
    ),
]

problems = []
for path in scan_files:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    rel = path.relative_to(cwd) if str(path).startswith(str(cwd)) else path
    for pattern, msg in patterns:
        if pattern.search(text):
            problems.append(f"{rel}: {msg}")

if any(path.suffix.lower() == ".py" for path in scan_files):
    python_cmd = sys.executable
    try:
        result = subprocess.run(
            [python_cmd, "-m", "compileall", "-q", "."],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            problems.append("python -m compileall -q . failed:\n" + (result.stderr or result.stdout)[-3000:])
    except Exception as exc:
        problems.append(f"compileall failed to run: {exc}")

state_dir = cwd / ".claude" / "state"
try:
    state_dir.mkdir(parents=True, exist_ok=True)
    if paths:
        changed = [str(p.relative_to(cwd)) if str(p).startswith(str(cwd)) else str(p) for p in paths]
        (state_dir / "needs_closing_review.txt").write_text("\n".join(changed), encoding="utf-8")
except Exception:
    pass

if problems:
    fail("\n\n".join(problems) + "\n\nFix these governance checks before closing the task.")

sys.exit(0)
