# candidate factor matrix

**Generated**: 2026-05-16T13:55:37.307442
**GP**: paused
**Phase 2**: paused

> Candidate factors are evaluated on train / validation / dev_test only.
> Final holdout is reported only for the frozen baseline.
> Train/validation rows use a frozen development universe and are diagnostic
> only, not pure walk-forward evidence.
> This does NOT approve Phase 2 or restart GP.

---

## 1. Setup

| Parameter | Value |
|-----------|-------|
| Universe | frozen_development_universe: U3_volclose_mid60, 2023-01-01 to 2025-12-31, 400 stocks |
| Universe note | Built once from whole dev period, not per-window; train/val rows are diagnostic |
| Cost | turnover * 0.004 |
| Portfolios | Long-only Top50, Top100 |
| Dev periods | train (2023-2024), validation (2024-2025), dev_test (2025H2) |
| Final holdout | Frozen baseline only, not used for selection |

## 2. Candidate Factor Families

| Family | Factors | Exposure Note |
|--------|---------|---------------|
| weekly_reversal | -ret_1w, -ret_4w, -ret_12w | Price momentum/reversal |
| weekly_volatility | -vol_4w, -vol_12w | Volatility premium |
| weekly_activity | -volume, -amount, volume_z, amount_z | May be liquidity/attention/size proxy, not clean alpha |
| daily_derived | d_ret_5d, d_ret_20d, d_vol_20d, d_downside_vol_20d, d_range_20d, d_intraday_strength_5d, d_volume_z20, d_amount_z20 | Pre-computed daily features |

## 3. Candidate vs Baseline (best IR per period)

Baseline factors: -volume, -ret_4w. New candidates: everything else.

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

## 5. Candidate Promotion Gate (dev_test only, no final_holdout)

Candidates are promoted only if they pass dev_test metrics, are not baseline/raw activity, and survive the walk-forward universe check.

| Category | Factor | TopN | IR vs EW | Excess Ann | Ex Win% | Turnover | Beats Baseline? | WF Gate | Promote? |
|----------|--------|------|----------|------------|---------|----------|-----------------|---------|----------|
| other_weekly | -ret_1w | 50 | -2.35 | -24.1% | 27% | 87% | N | N | N |
| other_weekly | -ret_1w | 100 | -2.35 | -17.4% | 27% | 78% | N | N | N |
| baseline | -ret_4w | 50 | -1.80 | -16.6% | 45% | 58% | N | N | N |
| baseline | -ret_4w | 100 | -2.20 | -13.0% | 32% | 45% | N | N | N |
| other_weekly | -ret_12w | 50 | +0.23 | +1.6% | 45% | 37% | N | N | N |
| other_weekly | -ret_12w | 100 | +0.28 | +1.8% | 45% | 28% | Y | N | N |
| other_weekly | -vol_4w | 50 | -1.42 | -10.8% | 30% | 49% | N | N | N |
| other_weekly | -vol_4w | 100 | -1.58 | -10.8% | 35% | 39% | N | N | N |
| other_weekly | -vol_12w | 50 | -1.79 | -18.2% | 30% | 17% | N | N | N |
| other_weekly | -vol_12w | 100 | -0.81 | -7.2% | 57% | 15% | N | N | N |
| baseline | -volume | 50 | +0.47 | +4.4% | 57% | 25% | N | N | N |
| baseline | -volume | 100 | +0.10 | +0.6% | 52% | 22% | N | N | N |
| raw_activity | -amount | 50 | +0.18 | +1.7% | 52% | 36% | N | N | N |
| raw_activity | -amount | 100 | -0.63 | -4.2% | 48% | 31% | N | N | N |
| raw_activity | volume_z | 50 | -0.20 | -2.1% | 48% | 59% | N | N | N |
| raw_activity | volume_z | 100 | -1.03 | -7.9% | 57% | 46% | N | N | N |
| raw_activity | amount_z | 50 | +0.16 | +1.9% | 52% | 57% | N | N | N |
| raw_activity | amount_z | 100 | -1.59 | -12.6% | 43% | 46% | N | N | N |
| daily_derived | d_ret_5d | 50 | -1.70 | -23.6% | 39% | 82% | N | N | N |
| daily_derived | d_ret_5d | 100 | -2.38 | -16.6% | 30% | 72% | N | N | N |
| daily_derived | d_ret_20d | 50 | +0.82 | +11.6% | 61% | 42% | Y | N | N |
| daily_derived | d_ret_20d | 100 | +0.98 | +7.5% | 57% | 37% | Y | N | N |
| daily_derived | d_vol_20d | 50 | -0.04 | -0.6% | 52% | 28% | N | N | N |
| daily_derived | d_vol_20d | 100 | +0.50 | +4.8% | 52% | 22% | Y | N | N |
| daily_derived | d_downside_vol_20d | 50 | -0.63 | -9.1% | 52% | 29% | N | N | N |
| daily_derived | d_downside_vol_20d | 100 | -0.69 | -7.6% | 52% | 23% | N | N | N |
| daily_derived | d_range_20d | 50 | +0.68 | +10.3% | 65% | 25% | Y | N | N |
| daily_derived | d_range_20d | 100 | +0.16 | +1.8% | 52% | 19% | Y | N | N |
| daily_derived | d_intraday_strength_5d | 50 | -2.61 | -27.6% | 35% | 90% | N | N | N |
| daily_derived | d_intraday_strength_5d | 100 | -2.48 | -16.9% | 30% | 77% | N | N | N |
| daily_derived | d_volume_z20 | 50 | -0.74 | -7.0% | 43% | 85% | N | N | N |
| daily_derived | d_volume_z20 | 100 | -0.80 | -5.1% | 48% | 69% | N | N | N |
| daily_derived | d_amount_z20 | 50 | -0.99 | -10.0% | 48% | 84% | N | N | N |
| daily_derived | d_amount_z20 | 100 | -0.84 | -5.5% | 52% | 68% | N | N | N |

**Exposure warning**: Raw activity factors (`-volume`, `-amount`, `volume_z`, `amount_z`) may proxy for liquidity, attention, or size. They require an exposure audit before being promoted beyond simple baselines.

**Promotion requires** (per candidate):
- IR vs EW > 0
- Positive excess annual return
- Weekly excess win rate > 50%
- Beats frozen baseline IR on dev_test
- No final_holdout used for selection
- Survives walk-forward universe check
- Is not a raw activity exposure candidate

## 6. Governance Gates

| Gate | Status |
|------|--------|
| Final holdout consistency | OK |
| Raw activity exposure audit | blocked_pending_neutralization_or_richer_exposure_audit |
| Walk-forward universe check | blocked_no_candidate_survived_walk_forward |
| light_model_scout | blocked |

## 7. Full Results

Parquet: `report/candidate_factor_matrix.parquet` (118 rows x 16 cols)

## 8. Status

| Item | Status |
|------|--------|
| GP | paused |
| Phase 2 | paused |
| Candidates evaluated | 102 |
| Baseline rows | 16 |

## 9. Generated Files

| File | Location |
|------|----------|
| Parquet | report/candidate_factor_matrix.parquet |
| Summary JSON | report/candidate_factor_matrix_summary.json |
| Report | report/candidate_factor_matrix.md |
| Report (analysis) | analysis/candidate_factor_matrix.md |
| Script | diagnostics/candidate_factor_matrix.py |
