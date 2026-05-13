# final holdout monitoring runbook

**Status**: preliminary pass. GP paused. Phase 2 paused.
**Scope**: -volume factor on U3_volclose_mid60, long-only Top50 equal weight.
**Holdout**: 2026-01-01+, untouched by any train/val/parameter selection.

---

## 1. Required data files

| File | Role |
|------|------|
| `data/weekly_daily_features.parquet` | Source data (qfq weekly bars + daily-derived features). Read-only. |
| `diagnostics/final_holdout_audit.py` | Reproducible script. |
| `diagnostics/followup_diagnosis.py` | Utility functions (imported). |

No other data or config files are needed. Token, universe, factor, portfolio,
and cost parameters are frozen in the script.

---

## 2. Regenerate final holdout reports

### Command

```powershell
python diagnostics\final_holdout_audit.py
```

Alternatively, use module syntax from repo root:

```bash
python -m diagnostics.final_holdout_audit
```

### Expected console output

The script prints a one-line summary of key metrics:

```text
Holdout: 13 weeks (2026-01-09 to 2026-04-30)
Cumulative: strat=+3.075% ew=+2.109% excess=+0.827%
Annualized: strat=+12.880% ew=+8.710% excess=+3.350%
IR vs EW: +0.4132
Relative max DD: -3.980%
Excess win rate: 61.5%
Turnover: 26.0%  Annual cost: +5.410%
Conclusion: preliminary pass
GP: paused  Phase 2: paused
```

### Expected output files

| File | Content |
|------|---------|
| `report/final_holdout_weekly_detail.parquet` | 13 rows: weekly strategy, EW, excess, NAV, turnover, cost |
| `report/final_holdout_metrics.json` | Single-source metrics dict |
| `report/final_holdout_volume_u3_lo50.md` | Formatted report |
| `report/final_holdout_audit.md` | Audit report |
| `analysis/final_holdout_volume_u3_lo50.md` | Report copy |
| `analysis/final_holdout_audit.md` | Audit copy |

Files under `report/` are gitignored and regenerated. Files under `analysis/`
are tracked in git.

---

## 3. Date conventions

| Column | Meaning |
|--------|---------|
| `signal_date` | Factor snapshot date. Week-end rebalance anchor. |
| `return_end_date` | End date of the forward return period (t+1 week-end). |

Returns are `t` signal to `t+1` forward, aligned to the weekly calendar.

Example: `signal_date=2026-01-09, return_end_date=2026-01-16` means the
factor was computed at the 2026-01-09 close, and the return covers the
week ending 2026-01-16.

---

## 4. Metrics to check

### Primary (must all stay positive)

| Metric | Current | Threshold |
|--------|---------|-----------|
| Annualized excess return vs EW | +3.4% | > 0 |
| IR vs EW | +0.41 | > 0 |
| Weekly excess win rate | 61.5% | > 50% |

### Secondary (monitor for drift)

| Metric | Current | Watch if |
|--------|---------|----------|
| Average turnover | 26.0% | > 40% |
| Annualized cost | 5.4% | > 10% |
| Relative max drawdown | -4.0% | < -10% |
| Absolute Sharpe | 0.54 | < 0 |
| Cumulative excess | +0.8% | < 0 |

---

## 5. What would downgrade preliminary pass

Any of the following on a regenerated report with fresh data:

- IR vs EW turns negative.
- Cumulative excess return turns negative.
- A new weekly detail row is computed from a different function or parameter set
  than the frozen ones in `diagnostics/final_holdout_audit.py`.
- Manual edits are made to the generated report numbers without regenerating
  from the script.

Market-driven underperformance (e.g., relative drawdown deepening to -8%) does
NOT automatically downgrade. The preliminary pass is about signal quality, not
a guarantee of future returns.

---

## 6. Evidence needed for final PASS

Before promoting `preliminary pass` to `PASS`, the following should be true:

1. At least 26 weekly observations (6 months of holdout) with IR vs EW > 0.
2. Cumulative excess return is still positive after 26+ weeks.
3. Walk-forward results are referenced alongside, not ignored. The 2023 failures
   remain a known regime risk.
4. All reports are regenerated from the single script, not manually edited.
5. There is no evidence that the signal is decaying with additional data.

Final PASS does not mean "this is a production strategy." It means the signal
has survived a meaningful out-of-sample window and the project can consider
Phase 2.

---

## 7. Lightweight integrity check

After regenerating, run:

```powershell
python diagnostics\final_holdout_monitor_check.py
```

This script loads the generated `report/final_holdout_metrics.json` and verifies:

- The file exists and is valid JSON.
- `ir_vs_ew > 0`, `annualized_excess_return > 0`, `weekly_excess_win_rate > 0.5`.
- `conclusion` is `preliminary pass`.
- `gp_status` and `phase2_status` are `paused`.
- No metric keys expected by the report are missing.

It does NOT recompute anything. It only validates the output of the main script.
Exit code 0 means the holdout status is consistent.

---

## 8. GP and Phase 2 status

```text
GP: paused
Phase 2: paused
```

Do not restart either unless:
- The final holdout is promoted to PASS by the evidence criteria above.
- The user explicitly requests it.
- There is a new audit confirming Phase 2 readiness.

---

## 9. Related documents

| Document | Role |
|----------|------|
| `analysis/final_diagnosis_report.md` | Full diagnosis + roadmap |
| `analysis/final_diagnosis_audit.md` | Audit of contradictions before Phase 1 |
| `analysis/walk_forward_baseline_report.md` | Walk-forward validation of simple baselines |
| `analysis/final_holdout_volume_u3_lo50.md` | Current final holdout result |
| `analysis/final_holdout_audit.md` | Audit of final holdout |
| `codexmd/CODEX_CLAUDE_HANDOFF.md` | Agent handoff notes |
