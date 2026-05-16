# raw activity exposure audit

**Generated**: 2026-05-16T14:00:32.477749
**GP**: paused
**Phase 2**: paused

> Raw activity factors are not clean alpha candidates by default.  This audit
> checks whether they are dominated by liquidity, attention, or price-level
> proxies before any promotion decision.

---

## 1. Gate Result

| Item | Status |
|------|--------|
| Raw activity gate | blocked_pending_neutralization_or_richer_exposure_audit |
| Final holdout used | False |
| Universe | frozen_development_universe: U3_volclose_mid60, 2023-01-01 to 2025-12-31 |
| Threshold | median abs Spearman >= 0.50 |

## 2. Factor Flags

| Factor | Max Median Abs Corr | Flagged Exposures | Promotion Allowed? |
|--------|---------------------|-------------------|--------------------|
| -amount | 1.00 | log_amount, log_vol_close, ret_4w | N |
| -volume | 1.00 | log_volume, price_level | N |
| amount_z | 0.73 | log_amount, log_vol_close, ret_4w | N |
| volume_z | 0.68 | log_amount, log_vol_close, ret_4w | N |

## 3. Strongest Exposure Relationships

| Period | Factor | Exposure | Mean Corr | Median Abs Corr | Weeks | Flagged |
|--------|--------|----------|-----------|-----------------|-------|---------|
| train | -volume | log_volume | -1.00 | 1.00 | 73 | Y |
| validation | -volume | log_volume | -1.00 | 1.00 | 50 | Y |
| dev_test | -volume | log_volume | -1.00 | 1.00 | 25 | Y |
| train | -amount | log_amount | -1.00 | 1.00 | 73 | Y |
| validation | -amount | log_amount | -1.00 | 1.00 | 50 | Y |
| dev_test | -amount | log_amount | -1.00 | 1.00 | 25 | Y |
| train | -amount | log_vol_close | -1.00 | 1.00 | 73 | Y |
| dev_test | -amount | log_vol_close | -1.00 | 1.00 | 25 | Y |
| validation | -amount | log_vol_close | -1.00 | 1.00 | 50 | Y |
| validation | -volume | price_level | +0.75 | 0.76 | 50 | Y |
| dev_test | amount_z | log_amount | +0.70 | 0.73 | 25 | Y |
| dev_test | amount_z | log_vol_close | +0.70 | 0.73 | 25 | Y |
| dev_test | -volume | price_level | +0.73 | 0.72 | 25 | Y |
| validation | amount_z | log_amount | +0.61 | 0.68 | 50 | Y |
| validation | amount_z | log_vol_close | +0.61 | 0.68 | 50 | Y |
| dev_test | volume_z | log_vol_close | +0.65 | 0.68 | 25 | Y |
| dev_test | volume_z | log_amount | +0.65 | 0.68 | 25 | Y |
| train | -volume | price_level | +0.66 | 0.67 | 73 | Y |
| validation | volume_z | log_vol_close | +0.59 | 0.64 | 50 | Y |
| validation | volume_z | log_amount | +0.59 | 0.64 | 50 | Y |

## 4. Interpretation

Raw activity candidates remain blocked from promotion unless a later audit
adds richer controls such as market capitalization, industry, liquidity, and
turnover neutralization.  This does not invalidate the frozen `-volume`
baseline; it prevents treating similar raw activity signals as newly promoted
model features.

## 5. Generated Files

| File | Location |
|------|----------|
| Parquet | report/activity_exposure_audit.parquet |
| Summary JSON | report/activity_exposure_audit_summary.json |
| Report | report/activity_exposure_audit.md |
| Report (analysis) | analysis/activity_exposure_audit.md |
| Script | diagnostics/activity_exposure_audit.py |
