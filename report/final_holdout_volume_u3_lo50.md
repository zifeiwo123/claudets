# final holdout: -volume on U3 LO50

**Generated**: 2026-05-13T18:30:46.993861
**Conclusion**: preliminary pass
**GP**: paused
**Phase 2**: paused

---

## Frozen Parameters

| Parameter | Value |
|-----------|-------|
| Universe | U3_volclose_mid60 (400 stocks) |
| Universe construction | Train 2023-01-01 to 2025-12-31, vol*close middle 60% |
| Factor | -volume |
| Portfolio | long_only_top50, equal weight |
| Benchmark | U3_volclose_mid60 equal-weight |
| Cost model | turnover * cost_rate |
| Holdout | 2026-01-01+ |

## Result

All numbers from single source: `report/final_holdout_weekly_detail.parquet` -> `report/final_holdout_metrics.json`.

| Metric | Value |
|--------|-------|
| Holdout weeks | 13 |
| First signal date | 2026-01-09 00:00:00 |
| Last signal date | 2026-04-30 00:00:00 |
| Cumulative strategy return | +3.075% |
| Cumulative universe EW return | +2.109% |
| Cumulative excess return | +0.827% |
| Annualized strategy return | +12.880% |
| Annualized universe EW return | +8.710% |
| **Annualized excess return vs EW** | **+3.350%** |
| Strategy Sharpe | 0.5385 |
| **Information Ratio vs EW** | **0.4132** |
| Strategy max drawdown | -11.310% |
| Universe EW max drawdown | -13.240% |
| **Relative max drawdown** | **-3.980%** |
| **Weekly excess win rate** | **61.5%** |
| Average turnover | 26.0% |
| Annualized cost | +5.410% |

## How annualized excess is computed

The annualized excess return is the annualized compound of the weekly active return series:

```text
excess_ret[t] = strategy_ret[t] - universe_ew_ret[t]
annualized_excess = annualize(compound(excess_ret))
```

It is NOT `annualized_strategy_return - annualized_universe_return`.
The latter would give +12.9% - (+8.7%) = +4.2%, which is a simple spread between two annualized numbers, not the annualized active return.

## Date convention

The `signal_date` column is the strategy rebalance date (week-end snapshot).
Returns are next-week forward returns aligned to that signal date.

```text
signal_date = t (factor snapshot date)
strategy_ret = portfolio return from t to t+1
universe_ew_ret = equal-weight return from t to t+1
excess_ret = strategy_ret - universe_ew_ret
```

## Pass/Fail Criteria

| Criterion | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| IR vs EW | > 0 | +0.41 | Pass |
| Excess annual return | > 0 | +3.350% | Pass |
| Excess win rate | > 50% | 61.5% | Pass |
| Single-source reproducibility | Same weekly detail | Confirmed | Pass |
| **Overall** | | | **preliminary pass** |

## Weekly Detail

Signal dates and next-week returns:

| signal_date | strategy_ret | universe_ew_ret | excess_ret | strategy_nav | universe_nav | active_nav | turnover | cost |
|-------------|--------------|-----------------|------------|--------------|--------------|------------|----------|------|
| 2026-01-09 | +0.628% | +0.336% | +0.292% | 1.006283 | 1.003362 | 1.002921 | 100.0% | 0.400% |
| 2026-01-16 | +1.187% | +3.512% | -2.326% | 1.018224 | 1.038602 | 0.979597 | 18.0% | 0.072% |
| 2026-01-23 | -4.033% | -3.497% | -0.536% | 0.977161 | 1.002285 | 0.974346 | 20.0% | 0.080% |
| 2026-02-06 | +1.564% | +1.075% | +0.489% | 0.992446 | 1.013061 | 0.979111 | 26.0% | 0.104% |
| 2026-02-13 | +1.929% | +3.512% | -1.583% | 1.011588 | 1.048638 | 0.963612 | 14.0% | 0.056% |
| 2026-02-27 | -3.325% | -3.263% | -0.062% | 0.977956 | 1.014419 | 0.963019 | 14.0% | 0.056% |
| 2026-03-06 | -1.216% | -1.679% | +0.464% | 0.966068 | 0.997383 | 0.967485 | 18.0% | 0.072% |
| 2026-03-13 | -4.300% | -5.452% | +1.152% | 0.924524 | 0.943007 | 0.978626 | 26.0% | 0.104% |
| 2026-03-20 | -0.426% | -0.596% | +0.171% | 0.920588 | 0.937383 | 0.980296 | 18.0% | 0.072% |
| 2026-03-27 | -1.907% | -2.944% | +1.037% | 0.903036 | 0.909786 | 0.990467 | 16.0% | 0.064% |
| 2026-04-03 | +7.224% | +5.257% | +1.966% | 0.968268 | 0.957618 | 1.009940 | 18.0% | 0.072% |
| 2026-04-10 | +2.286% | +2.641% | -0.356% | 0.990401 | 0.982913 | 1.006349 | 22.0% | 0.088% |
| 2026-04-30 | +4.074% | +3.884% | +0.190% | 1.030751 | 1.021086 | 1.008265 | 28.0% | 0.112% |

## Conclusion

The frozen -volume U3 LO50 baseline continues to show positive active performance through 2026-05-08 on the clean holdout. All active-performance criteria are met.

However:
- The holdout has only 13 weekly observations. Annualized metrics are indicative, not conclusive.
- Walk-forward showed regime dependency (2023 failures). A clean holdout in one regime does not erase this.
- The signal may degrade as 2026 data accumulates.

The result is a **preliminary pass**, not a final PASS. GP and Phase 2 remain paused.

## Files

| File | Source |
|------|--------|
| Weekly detail | report/final_holdout_weekly_detail.parquet |
| Metrics | report/final_holdout_metrics.json |
| Report | report/final_holdout_volume_u3_lo50.md |
| Report (analysis) | analysis/final_holdout_volume_u3_lo50.md |
| Audit report | report/final_holdout_audit.md |
| Audit report (analysis) | analysis/final_holdout_audit.md |
| Script | diagnostics/final_holdout_audit.py |
