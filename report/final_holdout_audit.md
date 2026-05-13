# final holdout audit

**Date**: 2026-05-13 18:20
**Scope**: `report/final_holdout_volume_u3_lo50.md`
**Decision**: downgrade PASS to **preliminary pass**
**GP status**: paused

---

## 1. What Was Audited

The audited claim was the frozen final holdout result for:

| Item | Value |
|------|-------|
| Universe | U3_volclose_mid60 |
| Universe train window | 2023-01-01 to 2025-12-31 |
| Factor | -volume |
| Portfolio | Long-only Top50 equal weight |
| Benchmark | U3 universe equal weight |
| Cost | turnover * 0.004 |
| Holdout | 2026-01-01+ |

The recent git path is:

| Commit | Role |
|--------|------|
| `5bac6d5` | Reconciled old contradictions and changed acceptance criteria to excess vs universe EW |
| `7dbb4ae` | Added walk-forward baseline validation and kept 2026-01+ untouched |
| `9c5fb2d` | Added final holdout report and marked it PASS |

The last step was too strong because the report table contained an inconsistent benchmark annual return.

## 2. Cross-Checks Performed

| Check | Source | Result |
|-------|--------|--------|
| Stored weekly detail | `report/final_holdout_weekly_detail.parquet` | 13 rows, metrics reproducible |
| Stored raw holdout data | `report/final_holdout_volume_u3_lo50.parquet` | Returns match weekly detail |
| Independent rebuild | `data/weekly_daily_features.parquet` | Rebuilt U3 universe, -volume Top50, forward returns; matches stored holdout rows |
| Report consistency | `report/final_holdout_volume_u3_lo50.md` | Found wrong Universe EW annual return |

The independent rebuild matched the stored holdout return rows to floating point tolerance. That supports the weekly return table, but not the old benchmark annual number.

## 3. Corrected Metrics

| Metric | Value |
|--------|-------|
| Holdout weeks | 13 |
| Cumulative strategy return | 3.075% |
| Cumulative universe EW return | 2.109% |
| Cumulative excess return | 0.826% |
| Annualized strategy return | 12.879% |
| Annualized universe EW return | 8.705% |
| Annualized excess return | 3.347% |
| IR vs EW | 0.413 |
| Strategy max drawdown | -11.313% |
| Universe EW max drawdown | -13.241% |
| Relative max drawdown | -3.979% |
| Weekly excess win rate | 61.538% |
| Average turnover | 26.000% |
| Annualized cost | 5.408% |

## 4. Why +12.9%, +8.7%, and +3.4% Can Coexist

The annualized excess return is computed from the weekly active return series:

```text
excess_ret_t = strategy_ret_t - universe_ew_ret_t
annualized_excess = annualize(compound(excess_ret_t))
```

It is not computed as:

```text
annualized_strategy_return - annualized_universe_return
```

For this holdout:

```text
annualized_strategy_return = +12.9%
annualized_universe_return = +8.7%
annualized_excess_return = +3.4%
simple annualized spread = +12.9% - +8.7% = +4.2%
```

The earlier combination of `strategy annual return = +12.9%`, `universe EW annual return = -31.6%`, and `excess annual return = +3.4%` cannot be reconciled under the same weekly return source. The `-31.6%` number is treated as stale or mis-sourced.

## 5. Weekly Detail

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

## 6. Residual Risks

- The stored date labels appear to be signal/rebalance dates, while the returns are next-week forward returns. This is acceptable only if reports state the alignment clearly.
- The old report included a material benchmark number not reproducible from the result source. Report generation should not manually paste metrics from separate runs.
- The holdout has only 13 weekly observations. IR and annualized returns are useful diagnostics, not a final production conclusion.
- The baseline is still regime-dependent based on walk-forward results. A clean final holdout does not erase 2023 failures.

## 7. Decision

The final holdout is a **preliminary pass**:

- Positive active return remains after correcting the benchmark number.
- All active-performance criteria are positive on the stored 13-week holdout.
- The previous PASS wording was too strong because one benchmark metric was wrong.

GP remains paused. Do not start Phase 2 until the report-generation path is made single-source and date labeling is reviewed.
