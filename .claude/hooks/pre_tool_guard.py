#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse guard for claudets.

Blocks destructive commands, direct edits to protected data/secrets, and long
experiment commands unless a recent preflight approval exists.
"""
import json
import os
import re
import sys
import time
from pathlib import Path


def block(msg: str) -> None:
    print("[claudets PreToolUse blocked]\n" + msg, file=sys.stderr)
    sys.exit(2)


def allow() -> None:
    sys.exit(0)


try:
    payload = json.load(sys.stdin)
except Exception as exc:
    block(f"Cannot parse hook input: {exc}")

tool = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {}) or {}
cwd = Path(payload.get("cwd") or os.getcwd())

if tool == "Bash":
    cmd = str(tool_input.get("command", ""))

    dangerous = [
        r"\brm\s+-rf\b",
        r"\bgit\s+reset\s+--hard\b",
        r"\bgit\s+clean\s+-fd\b",
        r"\bdel\s+/[sSqQ]\b",
        r"\brmdir\s+/[sSqQ]\b",
        r"\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b",
    ]
    if any(re.search(pattern, cmd, re.I) for pattern in dangerous):
        block("Dangerous command detected. Confirm backup and impact first:\n" + cmd)

    preflight_flag = cwd / ".claude" / ".preflight_ok"
    preflight_approved = False
    if preflight_flag.exists():
        try:
            preflight_approved = (time.time() - preflight_flag.stat().st_mtime) < 600
        except Exception:
            preflight_approved = False

    long_or_writing = [
        r"python\s+.*autonomous_loop\.py",
        r"python\s+.*main\.py",
        r"py\s+.*autonomous_loop\.py",
        r"py\s+.*main\.py",
    ]
    safe_keywords = ["compileall", "--help", "-h", "--dry-run", "pytest -q"]
    if (
        any(re.search(pattern, cmd, re.I) for pattern in long_or_writing)
        and not any(keyword in cmd for keyword in safe_keywords)
        and not preflight_approved
    ):
        block(
            "This command may run a long experiment or overwrite report outputs.\n"
            "Run /preflight first, or document the command, expected outputs, "
            "overwrite risk, and whether old reports need backup.\n"
            f"Command: {cmd}"
        )

    allow()

if tool in {"Edit", "Write", "MultiEdit"}:
    path = str(tool_input.get("file_path") or tool_input.get("path") or "").replace("\\", "/")
    lower_path = path.lower()

    protected = [
        ".env",
        "/secrets/",
        "credentials",
        ".git/",
        ".db",
        ".sqlite",
        ".parquet",
        "tushare_local",
        "daily_qfq",
        "adj_factor",
    ]
    if any(item in lower_path for item in protected):
        block(
            "Direct edits to secrets, source databases, or large result/data files are blocked:\n"
            f"{path}\nBack up and get explicit user approval if this is truly required."
        )

    text = ""
    for key in ("content", "new_string", "old_string"):
        val = tool_input.get(key)
        if isinstance(val, str):
            text += "\n" + val

    suspicious = [
        r"tushare.*token\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]",
        r"api[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        r"secret\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
    ]
    if any(re.search(pattern, text, re.I) for pattern in suspicious):
        block("Content appears to contain a token/api_key/secret. Use environment variables instead.")

    allow()

allow()
