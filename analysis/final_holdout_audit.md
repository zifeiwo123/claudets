# final holdout audit

**Generated**: 2026-05-13T22:25:52.355030
**Conclusion**: preliminary pass
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
| Holdout weeks | 13 |
| First signal date | 2026-01-09 00:00:00 |
| Last signal date | 2026-04-30 00:00:00 |
| First return end date | 2026-01-16 00:00:00 |
| Last return end date | 2026-05-08 00:00:00 |
| Cumulative strategy return | +3.075% |
| Cumulative universe EW return | +2.109% |
| Cumulative excess return | +0.827% |
| Annualized strategy return | +12.880% |
| Annualized universe EW return | +8.710% |
| Annualized excess return | +3.350% |
| IR vs EW | +0.4132 |
| Strategy max drawdown | -11.310% |
| Relative max drawdown | -3.980% |
| Weekly excess win rate | 61.5% |
| Average turnover | 26.0% |
| Annualized cost | +5.410% |

## Annualization Check

```text
excess_ret[t] = strategy_ret[t] - universe_ew_ret[t]
annualized_excess = compound(excess_ret) annualized to 52 weeks

NOT: annualized_strategy - annualized_universe
```

The simple spread is +12.9% - (+8.7%) = +4.2%.
The correct annualized excess is +3.350%.

## Date Convention

`signal_date` = factor snapshot date (week-end rebalance).
`return_end_date` = next available weekly close date.
Returns cover the interval from signal_date to return_end_date.

## Residual Risks

- Only 13 weekly observations.
- Walk-forward showed 2023 failures.
- Signal may decay as more 2026 data arrives.

## Decision

**preliminary pass**. GP paused. Phase 2 paused.
The baseline may be a candidate to beat, but it is not cleared as final.
