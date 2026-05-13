# final holdout: -volume on U3 LO50

**Date**: 2026-05-13 17:25
**Status**: PASS
**Rule**: Frozen. No parameter tuning allowed.

---

## Frozen Parameters

| Parameter | Value |
|-----------|-------|
| Universe | U3_volclose_mid60 (400 stocks) |
| Universe construction | Train 2023-01-01 to 2025-12-31, vol*close mid 60% |
| Factor | -volume |
| Portfolio | Long-only Top50, equal weight |
| Benchmark | U3 universe equal-weight |
| Cost model | turnover * 0.004 per rebalance |
| Holdout period | 2026-01-01+ |

## Result

| Metric | Value |
|--------|-------|
| Holdout weeks | 13 |
| Absolute annual return | 12.9% |
| Absolute Sharpe | 0.54 |
| Absolute max drawdown | -11.3% |
| Universe EW annual return | -31.6% |
| **Excess annual return vs EW** | **3.4%** |
| **Information Ratio vs EW** | **0.41** |
| **Relative max drawdown** | **-4.0%** |
| **Weekly excess win rate** | **61.5%** |
| Turnover | 26.0% |
| Annualized cost | 5.4% |

## Pass/Fail Criteria

| Criterion | Threshold | Actual | Pass? |
|-----------|-----------|--------|-------|
| IR vs EW | > 0 | +0.41 | Y |
| Excess annual return | > 0 | +3.4% | Y |
| Excess win rate | > 50% | 61.5% | Y |
| **OVERALL** | | | **PASS** |

## Conclusion: PASS

The frozen strategy passes final holdout validation.
The signal shows alpha beyond universe beta in the untouched 2026-01+ period.

- Phase 2 (feature expansion, GP) can now be considered
- -volume U3 LO50 is the baseline that any new factor must beat
- expansion must still pass walk-forward before replacing the baseline

## Weekly Detail

Full weekly data: 

## Files

| File | Location |
|------|----------|
| Report | report/final_holdout_volume_u3_lo50.md |
| Report (analysis) | analysis/final_holdout_volume_u3_lo50.md |
| Data | report/final_holdout_volume_u3_lo50.parquet |