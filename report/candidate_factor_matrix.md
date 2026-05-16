# candidate factor matrix

**Generated**: 2026-05-16T13:29:47.059688
**GP**: paused
**Phase 2**: paused

> Candidate factors are evaluated on train / validation / dev_test only.
> Final holdout is reported only for the frozen baseline.
> This does NOT approve Phase 2 or restart GP.

---

## 1. Setup

| Parameter | Value |
|-----------|-------|
| Universe | U3_volclose_mid60 (400 stocks) |
| Cost | turnover * 0.004 |
| Portfolios | Long-only Top50, Top100 |
| Dev periods | train (2023-2024), validation (2024-2025), dev_test (2025H2) |
| Final holdout | Frozen baseline only, not used for selection |

## 2. Candidate Factor Families

| Family | Factors |
|--------|---------|
| weekly_reversal | -ret_1w, -ret_4w, -ret_12w |
| weekly_volatility | -vol_4w, -vol_12w |
| weekly_activity | -volume, -amount, volume_z, amount_z |
| daily_derived | d_ret_5d, d_ret_20d, d_vol_20d, d_downside_vol_20d, d_range_20d, d_intraday_strength_5d, d_volume_z20, d_amount_z20 |

## 3. Candidate vs Baseline (best IR per period)

| Period+Portfolio | Best Candidate | Cand IR | Best Baseline | Base IR | Beats? |
|------------------|---------------|---------|---------------|---------|--------|
| train_LO50 | -amount | +1.90 | -ret_4w | -0.20 | > |
| train_LO100 | -amount | +2.62 | -volume | -0.03 | > |
| validation_LO50 | -amount | +5.44 | -volume | +1.52 | > |
| validation_LO100 | -amount | +5.52 | -volume | +1.27 | > |
| dev_test_LO50 | d_ret_20d | +0.82 | -volume | +0.47 | > |
| dev_test_LO100 | d_ret_20d | +0.98 | -volume | +0.10 | > |

## 4. Frozen Baseline on Final Holdout (untouched)

| Factor | TopN | Weeks | Excess Ann | IR vs EW | Ex Win% | Turnover |
|--------|------|-------|------------|----------|---------|----------|
| -volume | 50 | 13 | +3.4% | +0.41 | 61.5% | 26.0% |
| -volume | 100 | 13 | +15.4% | +2.56 | 61.5% | 21.1% |
| -ret_4w | 50 | 12 | -4.3% | -0.48 | 50.0% | 61.5% |
| -ret_4w | 100 | 12 | -7.1% | -0.97 | 41.7% | 51.9% |

## 5. Full Results

Parquet: `report/candidate_factor_matrix.parquet` (118 rows x 16 cols)

## 6. Status

| Item | Status |
|------|--------|
| GP | paused |
| Phase 2 | paused |
| Candidates evaluated | 102 |
| Baseline rows | 16 |

## 7. Generated Files

| File | Location |
|------|----------|
| Parquet | report/candidate_factor_matrix.parquet |
| Summary JSON | report/candidate_factor_matrix_summary.json |
| Report | report/candidate_factor_matrix.md |
| Report (analysis) | analysis/candidate_factor_matrix.md |
| Script | diagnostics/candidate_factor_matrix.py |
