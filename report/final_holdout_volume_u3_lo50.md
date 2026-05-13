# final holdout: -volume on U3 LO50

**Date**: 2026-05-13 18:20
**Status**: preliminary pass
**Rule**: Frozen. No parameter tuning allowed. GP remains paused.

---

## Frozen Parameters

| Parameter | Value |
|-----------|-------|
| Universe | U3_volclose_mid60 (400 stocks) |
| Universe construction | Train 2023-01-01 to 2025-12-31, vol*close middle 60% |
| Factor | -volume |
| Portfolio | Long-only Top50, equal weight |
| Benchmark | U3 universe equal-weight |
| Cost model | turnover * 0.004 per rebalance |
| Holdout period | 2026-01-01+ |

## Audit Finding

The previous report mixed an inconsistent benchmark number into the result table:

- Strategy annual return of **+12.9%** is correct.
- Excess annual return of **+3.4%** is correct when computed from the weekly active return series `strategy_ret - universe_ew_ret`.
- Universe EW annual return was previously shown as **-31.6%**. That is not consistent with the weekly detail table or with an independent rebuild from `data/weekly_daily_features.parquet`.
- The corrected Universe EW annual return for the same 13 holdout weeks is **+8.7%**.

The excess annual return is not calculated as `annualized_strategy_return - annualized_universe_return`. It is annualized from the compounded weekly excess series:

```text
3.4% = annualize(compound(weekly strategy_ret - weekly universe_ew_ret))
```

For reference, the simple difference between the two annualized returns is:

```text
12.9% - 8.7% = 4.2%
```

Because the previous benchmark annual return was wrong, the holdout is downgraded from PASS to **preliminary pass** pending one more implementation-level review of date labeling and benchmark generation.

## Corrected Result

| Metric | Value |
|--------|-------|
| Holdout weeks | 13 |
| Cumulative strategy return | 3.1% |
| Cumulative universe EW return | 2.1% |
| Cumulative excess return | 0.8% |
| Annualized strategy return | 12.9% |
| Annualized universe EW return | 8.7% |
| Annualized excess return vs EW | 3.4% |
| Absolute Sharpe | 0.54 |
| Information Ratio vs EW | 0.41 |
| Absolute max drawdown | -11.3% |
| Relative max drawdown | -4.0% |
| Weekly excess win rate | 61.5% |
| Average turnover | 26.0% |
| Annualized cost | 5.4% |

## Pass/Fail Criteria

| Criterion | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| IR vs EW | > 0 | +0.41 | Pass |
| Excess annual return | > 0 | +3.4% | Pass |
| Excess win rate | > 50% | 61.5% | Pass |
| Benchmark consistency | Same weekly detail source | Corrected | Needs review |
| Overall | | | **preliminary pass** |

## Weekly Detail

The `date` column is the strategy signal/rebalance date used in the stored holdout detail. Returns are next-week forward returns aligned to that signal date.

| date | strategy_ret | universe_ew_ret | excess_ret | strategy_nav | universe_nav | active_nav | turnover | cost |
|------|--------------|-----------------|------------|--------------|--------------|------------|----------|------|
| 2026-01-09 | 0.628% | 0.336% | 0.292% | 1.006283 | 1.003362 | 1.002921 | 100.0% | 0.400% |
| 2026-01-16 | 1.187% | 3.512% | -2.326% | 1.018224 | 1.038602 | 0.979597 | 18.0% | 0.072% |
| 2026-01-23 | -4.033% | -3.497% | -0.536% | 0.977161 | 1.002285 | 0.974346 | 20.0% | 0.080% |
| 2026-02-06 | 1.564% | 1.075% | 0.489% | 0.992446 | 1.013061 | 0.979111 | 26.0% | 0.104% |
| 2026-02-13 | 1.929% | 3.512% | -1.583% | 1.011588 | 1.048638 | 0.963612 | 14.0% | 0.056% |
| 2026-02-27 | -3.325% | -3.263% | -0.062% | 0.977956 | 1.014419 | 0.963019 | 14.0% | 0.056% |
| 2026-03-06 | -1.216% | -1.679% | 0.464% | 0.966068 | 0.997383 | 0.967485 | 18.0% | 0.072% |
| 2026-03-13 | -4.300% | -5.452% | 1.152% | 0.924524 | 0.943007 | 0.978626 | 26.0% | 0.104% |
| 2026-03-20 | -0.426% | -0.596% | 0.171% | 0.920588 | 0.937383 | 0.980296 | 18.0% | 0.072% |
| 2026-03-27 | -1.907% | -2.944% | 1.037% | 0.903036 | 0.909786 | 0.990467 | 16.0% | 0.064% |
| 2026-04-03 | 7.224% | 5.257% | 1.966% | 0.968268 | 0.957618 | 1.009940 | 18.0% | 0.072% |
| 2026-04-10 | 2.286% | 2.641% | -0.356% | 0.990401 | 0.982913 | 1.006349 | 22.0% | 0.088% |
| 2026-04-30 | 4.074% | 3.884% | 0.190% | 1.030751 | 1.021086 | 1.008265 | 28.0% | 0.112% |

## Conclusion

The frozen -volume U3 LO50 baseline still has positive active performance in the 2026-01+ holdout after correcting the benchmark annual return. However, the previous report contained a material benchmark inconsistency, so the result should be treated as **preliminary pass**, not a final PASS.

- Phase 2 and GP remain paused.
- This baseline may remain the candidate to beat, but it is not yet cleared as a final accepted baseline.
- Any future report must keep strategy, benchmark, excess, NAV, turnover, and cost in one auditable result source.

## Files

| File | Location |
|------|----------|
| Report | report/final_holdout_volume_u3_lo50.md |
| Report (analysis) | analysis/final_holdout_volume_u3_lo50.md |
| Audit | report/final_holdout_audit.md |
| Detail data | report/final_holdout_weekly_detail.parquet |
| Raw holdout data | report/final_holdout_volume_u3_lo50.parquet |
