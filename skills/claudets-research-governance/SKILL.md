---
name: claudets-research-governance
description: Use when working in the claudets A-share weekly alpha research repo, especially for factor research, data contracts, backtests, report generation, holdout audits, git commits, or when changing AGENTS.md/CLAUDE.md/Codex rules. Enforces reproducible research, UTF-8-safe editing, single-source metrics, GP pause discipline, and clear PASS/preliminary status language.
---

# Claudets Research Governance

## Purpose

Use this skill before changing code, reports, generated experiment outputs, or agent instructions in `claudets`.

The goal is not to improve one backtest number. The goal is to preserve a reproducible A-share weekly alpha research system with truthful reports.

## Preflight

Before editing, answer these five checks in your working notes:

1. Which module is affected: data, factors, evaluation, portfolio, pipeline, report, docs, or agent config?
2. Does the change affect adjusted prices, trading dates, forward-return alignment, universe construction, or source-data read/write boundaries?
3. Does it affect IC, stratification, long-short, long-only, cost, turnover, drawdown, benchmark, or active-return metrics?
4. Does it affect `report/`, `analysis/`, `summary`, parquet, CSV, or markdown outputs?
5. Does the conclusion require rerunning an experiment, or only recalculating/reporting existing result data?

## Encoding Rules

- Treat repository text files as UTF-8.
- If a file displays mojibake or broken Chinese, do not append more mixed-encoding text. Prefer replacing the touched section with clean UTF-8 or ASCII.
- Use ASCII for new governance docs unless Chinese wording is required by the user.
- Before committing edited docs or Python files, scan touched files for obvious mojibake markers, replacement characters, or unterminated f-strings caused by corrupted text.
- Do not use PowerShell `Get-Content` output alone to decide whether a UTF-8 file is corrupt. Cross-check with Python UTF-8 reads or git diff.

## Research Guardrails

- GP remains paused unless the user explicitly asks to restart it after a documented audit.
- Do not enter Phase 2 after a single holdout pass. Require a clean audit trail and stable baseline comparison.
- Long-short and long-only results must be reported separately.
- A-share practical candidate reports should prefer long-only TopN/Top% portfolios.
- Universe construction must be train-only or point-in-time rolling. Never use future validation/test information to select the universe.
- Default signal/return alignment is `t` week signal to `t+1` week holding return. Report date labels must state whether they are signal dates or realization dates.
- Transaction cost must be subtractive: `net_ret = gross_ret - turnover * cost_rate`.
- Drawdown control must use historical information only. Never clip realized returns to improve a report.

## Report Rules

Use one result source per report. If a report contains strategy, benchmark, excess, NAV, turnover, and cost, all of them must come from the same table or a documented deterministic rebuild.

For each audited report, include:

- frozen parameters
- source tables used
- exact train, validation, test, and holdout dates
- strategy return, benchmark return, active return, NAV, turnover, and cost definitions
- cumulative and annualized strategy return
- cumulative and annualized benchmark return
- cumulative and annualized excess return
- IR vs benchmark
- relative max drawdown
- pass status and residual risks

Status language:

- Use `PASS` only when all metrics are single-source reproducible and no material inconsistency remains.
- Use `preliminary pass` when active metrics look positive but any metric, label, date alignment, or report-generation path still needs review.
- Use `engineering-only` when qfq status, source data, or implementation path is not verified.

## Holdout Audit Workflow

For final holdout claims:

1. Read the committed report and the generated result data if present.
2. Recompute metrics from the weekly detail table.
3. Independently rebuild the candidate from source feature data when feasible.
4. Compare strategy, universe EW, excess, turnover, and cost row by row.
5. Explain annualized excess carefully: it is annualized from weekly active returns, not the difference between two annualized return numbers.
6. If any table metric is wrong, downgrade status to `preliminary pass` and create an audit report.
7. Keep GP paused until the audit and report-generation path are clean.

## Git Handoff

Before commit:

- Show changed files with `git status --short`.
- Review diffs for touched reports and instructions.
- Run the narrowest available validation. If full `compileall` fails because unrelated existing files are corrupt, state that clearly and run targeted checks on changed files.
- Commit only related files. Do not stage generated caches or ignored local tool folders.

Final handoff must say:

- files changed
- why they changed
- checks run
- whether backtests or GP were rerun
- conclusions that still cannot be used
- next recommended action
