# exposure neutralization readiness

**Generated**: 2026-05-16T14:13:29.537147
**neutralization_ready**: false
**GP**: paused
**Phase 2**: paused

> Audits local data only. Does not download new data.
> Final holdout untouched.

---

## 1. Local Data Files Audited

| File | Rows | Stocks | Columns |
|------|------|--------|---------|
| data/daily_ohlcv.parquet | 4,272,733 | 5515 | 8 cols |
| data/weekly_ohlcv.parquet | 871,552 | 5512 | 9 cols |
| data/weekly_daily_features.parquet | 871,552 | 5512 | 17 cols |
| data/hs300_weekly.parquet | 44 | 1 | 11 cols |
| data/cyb_weekly.parquet | 44 | 1 | 11 cols |

## 2. Exposure Field Audit

| Field | Description | Status | Source API |
|-------|-------------|--------|------------|
| total_mv | total market cap | ABSENT | Tushare daily_basic or pro_bar |
| circ_mv | circulating market cap | ABSENT | Tushare daily_basic or pro_bar |
| industry | sector / industry classification | ABSENT | Tushare stock_basic or index_classify |
| is_st | ST / *ST flag | ABSENT | Tushare namechange or daily_basic |
| suspended | suspension flag | PROXY: n_days | Tushare suspend or trade_cal |
| turnover_rate | turnover rate (volume / float) | ABSENT | Tushare daily_basic |
| float_share | circulating shares | ABSENT | Tushare daily_basic |
| list_date | listing date | ABSENT | Tushare stock_basic |
| list_status | listing status (L/D/P) | ABSENT | Tushare stock_basic |

## 3. Existing Computable Proxies

| Name | Source | Use |
|------|--------|-----|
| n_days | weekly_ohlcv.parquet | proxy for listing recency and suspension (fewer days = newer or suspended) |
| volume * close | weekly_ohlcv.parquet | trading-value proxy, used in U3 universe, NOT a market cap proxy |
| amount | weekly_ohlcv.parquet | daily turnover in CNY, liquidity proxy, NOT a size proxy |

## 4. Critical Fields Missing

4 critical fields are absent with no acceptable proxy:

- total_mv
- circ_mv
- industry
- is_st

## 5. Recommendation

Neutralization is blocked. To proceed, download from Tushare: stock_basic (industry, list_date, list_status), daily_basic (total_mv, circ_mv, turnover_rate), and namechange (ST flags). Do not infer market cap from amount/volume.

## 6. Decision

| Item | Value |
|------|-------|
| neutralization_ready | **false** |
| Hard blocker | **Yes** |
| Raw activity promotion | blocked |
| light_model_scout | blocked |
| GP | paused |
| Phase 2 | paused |

## 7. Generated Files

| File | Location |
|------|----------|
| JSON | report/exposure_neutralization_readiness.json |
| Report | report/exposure_neutralization_readiness.md |
| Report (analysis) | analysis/exposure_neutralization_readiness.md |
| Script | diagnostics/exposure_neutralization_readiness.py |
