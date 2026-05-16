# exposure controls data contract

**Generated**: 2026-05-16T14:22:45.654852
**data_contract_ready**: true
**download_performed**: false
**neutralization_ready**: false
**GP**: paused
**Phase 2**: paused

> Defines required schemas for future exposure-control staging tables.
> Does NOT download data. Does NOT modify source parquet files.
> Raw activity factors remain blocked until true exposure controls are loaded.

---

## 1. Required Future Datasets

| Dataset | Source API | Frequency | Suggested File | Columns |
|---------|-----------|-----------|---------------|---------|
| stock_basic | Tushare stock_basic | static (one row per stock, refreshed periodically) | data/exposure_controls/stock_basic.parquet | ts_code, name, industry, list_date, list_status |
| daily_basic | Tushare daily_basic | daily (one row per stock per trading day) | data/exposure_controls/daily_basic.parquet | ts_code, trade_date, total_mv, circ_mv, turnover_rate, float_share |
| namechange_or_st | Tushare namechange | event-driven (one row per name-change event) | data/exposure_controls/namechange_or_st.parquet | ts_code, start_date, end_date, name, is_st |
| suspend_or_trade_status | Tushare suspend_d or trade_cal | daily (one row per stock per day when status known) | data/exposure_controls/suspend_or_trade_status.parquet | ts_code, trade_date, suspended |

## 2. Staging Directory

| Item | Value |
|------|-------|
| Path | data\exposure_controls |
| Status | directory absent |

## 3. Join Policy

Signals at week t may only use exposure controls known on or before signal_date. For daily_basic: use the most recent trade_date <= signal_date. For namechange_or_st: use rows where start_date <= signal_date and (end_date is null or end_date >= signal_date). For suspend_or_trade_status: use the trade_date matching signal_date. No final_holdout-based candidate selection. No forward-looking join: future exposure data must not leak into historical signal dates.

## 4. Source Files Protected (must not be modified)

- data/daily_ohlcv.parquet
- data/weekly_ohlcv.parquet
- data/weekly_daily_features.parquet

## 5. Download Steps

1. Confirm TUSHARE_TOKEN is set in environment.
2. Run a download script (not yet built) that fetches:
   - stock_basic   -> data/exposure_controls/stock_basic.parquet
   - daily_basic    -> data/exposure_controls/daily_basic.parquet
   - namechange     -> data/exposure_controls/namechange_or_st.parquet
   - suspend_d      -> data/exposure_controls/suspend_or_trade_status.parquet
3. Validate column presence and types.
4. Re-run exposure_neutralization_readiness.py to confirm    neutralization_ready flips to true.
5. Only then build neutralized candidate tests.

## 6. Schema Validation

| Item | Value |
|------|-------|
| Valid | Yes |
| Errors | 0 |

## 7. Current Blockers

| Gate | Status |
|------|--------|
| data_contract_ready | true |
| download_performed | false |
| neutralization_ready | false |
| Raw activity promotion | blocked |
| light_model_scout | blocked |
| GP | paused |
| Phase 2 | paused |

## 8. Generated Files

| File | Location |
|------|----------|
| JSON | report/exposure_controls_data_contract.json |
| Report | report/exposure_controls_data_contract.md |
| Report (analysis) | analysis/exposure_controls_data_contract.md |
| Script | diagnostics/exposure_controls_data_contract.py |
