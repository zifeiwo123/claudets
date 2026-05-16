# model research readiness

**Generated**: 2026-05-16T13:54:57.036866
**GP**: paused
**Phase 2**: paused

> This prepares model comparison. It does NOT approve Phase 2, does NOT
> restart GP, and does NOT tune on the final holdout period.

---

## 1. Data Summary

| Item | Value |
|------|-------|
| Source | data/weekly_daily_features.parquet |
| Total rows | 871,552 |
| Date range | 2023-01-05 to 2026-05-08 |
| Feature columns | 8 (d_ret_5d, d_ret_20d, d_vol_20d, d_downside_vol_20d, d_range_20d, d_intraday_strength_5d, d_volume_z20, d_amount_z20) |

## 2. Period Definitions

| Period | Start | End | Role |
|--------|-------|-----|------|
| train | 2023-01-01 | 2024-06-30 | Universe + baseline dev |
| validation | 2024-07-01 | 2025-06-30 | Factor selection |
| dev_test | 2025-07-01 | 2025-12-31 | Development test |
| final_holdout | 2026-01-01 | data_end | Frozen, untuned |

## 3. Column Coverage by Period

| Period | Rows | Stocks | Weeks | d_ret_5d | d_ret_20d | d_vol_20d | d_downside_vol_20d | d_range_20d | d_intraday_strength_5d | d_volume_z20 | d_amount_z20 |
| train | 376295 | 5291 | 122 | 99% | 94% | 97% | 97% | 97% | 100% | 97% | 97% |
| validation | 266755 | 5397 | 101 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| dev_test | 135407 | 5458 | 56 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| final_holdout | 93095 | 5512 | 38 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

## 4. Frozen Baseline Configuration

| Parameter | Value |
|-----------|-------|
| Universe | U3_volclose_mid60 |
| Universe train | 2023-01-01 to 2025-12-31 |
| Universe disclosure | frozen_development_universe; train/validation rows are diagnostic, not pure walk-forward evidence |
| Universe size | 400 stocks |
| Factors | -volume, -ret_4w |
| Portfolios | long_only_top50, long_only_top100 |
| Benchmark | universe_equal_weight |
| Cost | turnover * cost_rate |

## 5. Frozen Baseline Results (all periods)

| Period | Factor | TopN | Wks | Abs Ann | Abs Sharpe | EW Ann | Excess Ann | IR vs EW | Ex Win% | Turnover |
|--------|--------|------|-----|---------|-----------|--------|------------|----------|---------|----------|
| train | -volume | 50 | 70 | -15.1% | -0.55 | -8.6% | -6.4% | -0.59 | 44.3% | 20.0% |
| train | -volume | 100 | 70 | -9.2% | -0.37 | -8.6% | -0.2% | -0.03 | 47.1% | 16.5% |
| validation | -volume | 50 | 47 | +84.0% | +2.70 | +60.4% | +15.1% | +1.52 | 55.3% | 22.2% |
| validation | -volume | 100 | 47 | +75.6% | +2.59 | +60.4% | +9.4% | +1.27 | 48.9% | 17.5% |
| dev_test | -volume | 50 | 23 | +57.7% | +2.99 | +51.5% | +4.4% | +0.47 | 56.5% | 25.1% |
| dev_test | -volume | 100 | 23 | +51.9% | +2.81 | +51.5% | +0.6% | +0.10 | 52.2% | 21.6% |
| final_holdout | -volume | 50 | 13 | +12.9% | +0.54 | +8.7% | +3.4% | +0.41 | 61.5% | 26.0% |
| final_holdout | -volume | 100 | 13 | +25.8% | +1.06 | +8.7% | +15.4% | +2.56 | 61.5% | 21.1% |
| train | -ret_4w | 50 | 63 | -14.3% | -0.41 | -9.4% | -3.6% | -0.20 | 41.3% | 50.0% |
| train | -ret_4w | 100 | 63 | -18.4% | -0.59 | -9.4% | -8.7% | -0.60 | 39.7% | 39.4% |
| validation | -ret_4w | 50 | 44 | +22.1% | +0.84 | +37.0% | -11.1% | -1.02 | 40.9% | 53.5% |
| validation | -ret_4w | 100 | 44 | +33.3% | +1.33 | +37.0% | -2.9% | -0.35 | 43.2% | 43.5% |
| dev_test | -ret_4w | 50 | 22 | +20.4% | +1.07 | +44.4% | -16.6% | -1.80 | 45.5% | 57.7% |
| dev_test | -ret_4w | 100 | 22 | +25.8% | +1.53 | +44.4% | -13.0% | -2.20 | 31.8% | 44.5% |
| final_holdout | -ret_4w | 50 | 12 | +12.8% | +0.48 | +17.8% | -4.3% | -0.48 | 50.0% | 61.5% |
| final_holdout | -ret_4w | 100 | 12 | +9.5% | +0.36 | +17.8% | -7.1% | -0.97 | 41.7% | 51.9% |

## 6. Status

| Item | Status |
|------|--------|
| GP | paused |
| Phase 2 | paused |
| Final holdout tuning | Not performed |
| Final holdout consistency | OK |

## 7. Generated Files

| File | Location |
|------|----------|
| JSON metrics | report/model_research_readiness.json |
| Report | report/model_research_readiness.md |
| Report (analysis) | analysis/model_research_readiness.md |
| Script | diagnostics/model_research_readiness.py |
