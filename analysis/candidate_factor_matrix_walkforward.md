# candidate factor matrix walk-forward universe check

**Generated**: 2026-05-16T14:00:41.810826
**GP**: paused
**Phase 2**: paused

> This is a pre-model-scout gate.  Each window rebuilds the U3 universe from
> train-only data, evaluates candidates on the following validation period,
> and never uses final_holdout for candidate selection.

---

## 1. Gate Result

| Gate | Status |
|------|--------|
| Final holdout used | False |
| Universe | U3_volclose_mid60 rebuilt per window from train-only data |
| light_model_scout | blocked_no_candidate_survived_walk_forward |

## 2. Surviving New Candidates

No non-baseline, non-raw-activity candidate passes at least 3 of 5 windows.

Survival rule: non-baseline, non-raw-activity candidate must pass at least
3 of 5 windows.  A window pass requires IR vs EW > 0, positive annualized
excess return, excess win rate > 50%, and IR above the best frozen baseline
for the same window and TopN.

## 3. Top Walk-forward Rows

| Category | Factor | TopN | Passes | Mean IR | Mean Excess Ann | Mean Turnover | Survives? |
|----------|--------|------|--------|---------|-----------------|---------------|-----------|
| raw_activity | -amount | 100 | 4/5 | +1.85 | +12.6% | 29.4% | N |
| raw_activity | -amount | 50 | 3/5 | +2.31 | +17.8% | 35.1% | N |
| other_weekly | -ret_12w | 50 | 1/5 | +0.35 | -0.7% | 37.7% | N |
| other_weekly | -ret_12w | 100 | 1/5 | +0.09 | -2.0% | 30.7% | N |
| other_weekly | -vol_12w | 50 | 1/5 | -0.25 | -2.0% | 21.6% | N |
| other_weekly | -vol_12w | 100 | 1/5 | -0.29 | -1.8% | 17.4% | N |
| daily_derived | d_vol_20d | 100 | 1/5 | -0.62 | -8.6% | 22.8% | N |
| other_weekly | -vol_4w | 100 | 1/5 | -0.63 | -4.2% | 41.7% | N |
| other_weekly | -vol_4w | 50 | 1/5 | -0.75 | -6.6% | 53.6% | N |
| daily_derived | d_range_20d | 100 | 1/5 | -0.77 | -9.8% | 19.0% | N |
| daily_derived | d_ret_20d | 100 | 1/5 | -1.23 | -14.8% | 38.7% | N |
| daily_derived | d_ret_20d | 50 | 1/5 | -1.65 | -26.3% | 45.8% | N |
| baseline | -volume | 100 | 0/5 | +0.21 | +0.4% | 19.4% | N |
| baseline | -volume | 50 | 0/5 | +0.18 | -0.4% | 23.8% | N |
| baseline | -ret_4w | 100 | 0/5 | -0.59 | -4.2% | 45.0% | N |
| baseline | -ret_4w | 50 | 0/5 | -0.61 | -6.0% | 56.3% | N |
| daily_derived | d_downside_vol_20d | 50 | 0/5 | -0.70 | -10.4% | 28.9% | N |
| daily_derived | d_downside_vol_20d | 100 | 0/5 | -0.82 | -9.3% | 24.1% | N |
| other_weekly | -ret_1w | 100 | 0/5 | -0.95 | -9.5% | 77.1% | N |
| other_weekly | -ret_1w | 50 | 0/5 | -1.17 | -15.7% | 86.7% | N |

## 4. Governance

- This check does not approve Phase 2.
- This check does not restart GP.
- If a candidate survives, a human still needs to approve any bounded
  `diagnostics/light_model_scout.py` run.
- Raw activity candidates remain blocked pending exposure review.

## 5. Generated Files

| File | Location |
|------|----------|
| Parquet | report/candidate_factor_matrix_walkforward.parquet |
| Summary JSON | report/candidate_factor_matrix_walkforward_summary.json |
| Report | report/candidate_factor_matrix_walkforward.md |
| Report (analysis) | analysis/candidate_factor_matrix_walkforward.md |
| Script | diagnostics/candidate_factor_matrix_walkforward.py |
