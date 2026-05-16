"""Exposure-controls data contract and staging plan.

Defines required schemas for future local staging tables. Does NOT
download data. Validates only that schemas are well-formed.

Intended storage: data/exposure_controls/ (separate from source parquets).

Outputs:
  report/exposure_controls_data_contract.json
  report/exposure_controls_data_contract.md
  analysis/exposure_controls_data_contract.md
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"

os.makedirs(REPORT_DIR, exist_ok=True)

EXPOSURE_STAGING_DIR = os.path.join("data", "exposure_controls")

SCHEMAS = {
    "stock_basic": {
        "description": "Stock basic info: industry, listing date, status",
        "source_api": "Tushare stock_basic",
        "frequency": "static (one row per stock, refreshed periodically)",
        "columns": [
            ("ts_code", "str", "stock code, e.g. 000001.SZ"),
            ("name", "str", "stock name"),
            ("industry", "str", "industry/sector classification"),
            ("list_date", "str", "listing date YYYYMMDD"),
            ("list_status", "str", "L=listed, D=delisted, P=paused"),
        ],
        "primary_key": ["ts_code"],
        "join_key": "ts_code",
        "suggested_file": "data/exposure_controls/stock_basic.parquet",
    },
    "daily_basic": {
        "description": "Daily market cap, turnover rate, float shares",
        "source_api": "Tushare daily_basic",
        "frequency": "daily (one row per stock per trading day)",
        "columns": [
            ("ts_code", "str", "stock code"),
            ("trade_date", "str", "trading date YYYYMMDD"),
            ("total_mv", "float64", "total market cap (10k CNY)"),
            ("circ_mv", "float64", "circulating market cap (10k CNY)"),
            ("turnover_rate", "float64", "turnover rate (percent)"),
            ("float_share", "float64", "circulating shares (10k shares)"),
        ],
        "primary_key": ["ts_code", "trade_date"],
        "join_key": "ts_code",
        "suggested_file": "data/exposure_controls/daily_basic.parquet",
    },
    "namechange_or_st": {
        "description": "Name change history with ST flag derivation",
        "source_api": "Tushare namechange",
        "frequency": "event-driven (one row per name-change event)",
        "columns": [
            ("ts_code", "str", "stock code"),
            ("start_date", "str", "effective start date YYYYMMDD"),
            ("end_date", "str", "effective end date YYYYMMDD (null if current)"),
            ("name", "str", "stock name at that time"),
            ("is_st", "int", "1 if name contains ST/*ST/SST, 0 otherwise"),
        ],
        "primary_key": ["ts_code", "start_date"],
        "join_key": "ts_code",
        "suggested_file": "data/exposure_controls/namechange_or_st.parquet",
    },
    "suspend_or_trade_status": {
        "description": "Suspension status per stock per day",
        "source_api": "Tushare suspend_d or trade_cal",
        "frequency": "daily (one row per stock per day when status known)",
        "columns": [
            ("ts_code", "str", "stock code"),
            ("trade_date", "str", "trading date YYYYMMDD"),
            ("suspended", "int", "1 if suspended on this date, 0 if trading"),
        ],
        "primary_key": ["ts_code", "trade_date"],
        "join_key": "ts_code",
        "suggested_file": "data/exposure_controls/suspend_or_trade_status.parquet",
    },
}

JOIN_POLICY = (
    "Signals at week t may only use exposure controls known on or before "
    "signal_date. For daily_basic: use the most recent trade_date <= "
    "signal_date. For namechange_or_st: use rows where start_date <= "
    "signal_date and (end_date is null or end_date >= signal_date). "
    "For suspend_or_trade_status: use the trade_date matching signal_date. "
    "No final_holdout-based candidate selection. "
    "No forward-looking join: future exposure data must not leak into "
    "historical signal dates."
)

SOURCE_FILES_PROTECTED = [
    "data/daily_ohlcv.parquet",
    "data/weekly_ohlcv.parquet",
    "data/weekly_daily_features.parquet",
]


def compute_all():
    schemas_valid = True
    schema_errors = []
    for name, schema in SCHEMAS.items():
        if "columns" not in schema or len(schema["columns"]) == 0:
            schemas_valid = False
            schema_errors.append(f"{name}: no columns defined")
        if "primary_key" not in schema:
            schema_errors.append(f"{name}: no primary_key defined")
        if "join_key" not in schema:
            schema_errors.append(f"{name}: no join_key defined")

    staging_exists = os.path.isdir(EXPOSURE_STAGING_DIR)
    staging_files = []
    if staging_exists:
        staging_files = os.listdir(EXPOSURE_STAGING_DIR)

    result = {
        "generated_at": datetime.now().isoformat(),
        "data_contract_ready": True,
        "download_performed": False,
        "neutralization_ready": False,
        "schemas": {},
        "schema_validation": {
            "valid": schemas_valid,
            "errors": schema_errors,
        },
        "staging": {
            "path": EXPOSURE_STAGING_DIR,
            "exists": staging_exists,
            "files_present": staging_files,
        },
        "join_policy": JOIN_POLICY,
        "source_files_protected": SOURCE_FILES_PROTECTED,
        "download_steps": [
            "1. Confirm TUSHARE_TOKEN is set in environment.",
            "2. Run a download script (not yet built) that fetches:",
            "   - stock_basic   -> data/exposure_controls/stock_basic.parquet",
            "   - daily_basic    -> data/exposure_controls/daily_basic.parquet",
            "   - namechange     -> data/exposure_controls/namechange_or_st.parquet",
            "   - suspend_d      -> data/exposure_controls/suspend_or_trade_status.parquet",
            "3. Validate column presence and types.",
            "4. Re-run exposure_neutralization_readiness.py to confirm "
            "   neutralization_ready flips to true.",
            "5. Only then build neutralized candidate tests.",
        ],
        "gp_status": "paused",
        "phase2_status": "paused",
    }

    for name, schema in SCHEMAS.items():
        result["schemas"][name] = {
            "description": schema["description"],
            "source_api": schema["source_api"],
            "frequency": schema["frequency"],
            "columns": [{"name": c[0], "dtype": c[1], "description": c[2]} for c in schema["columns"]],
            "primary_key": schema["primary_key"],
            "join_key": schema["join_key"],
            "suggested_file": schema["suggested_file"],
        }

    json_path = os.path.join(REPORT_DIR, "exposure_controls_data_contract.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def generate_report(result):
    r = result

    schema_rows = []
    for name, s in r["schemas"].items():
        col_list = ", ".join(c["name"] for c in s["columns"])
        schema_rows.append(
            f"| {name} | {s['source_api']} | {s['frequency']} | "
            f"{s['suggested_file']} | {col_list} |"
        )

    staging_status = f"{len(r['staging']['files_present'])} files present" if r["staging"]["exists"] else "directory absent"
    contract_ready = "true" if r["data_contract_ready"] else "false"
    dl_performed = "true" if r["download_performed"] else "false"
    neut_ready = "true" if r["neutralization_ready"] else "false"

    report = f"""# exposure controls data contract

**Generated**: {r['generated_at']}
**data_contract_ready**: {contract_ready}
**download_performed**: {dl_performed}
**neutralization_ready**: {neut_ready}
**GP**: {r['gp_status']}
**Phase 2**: {r['phase2_status']}

> Defines required schemas for future exposure-control staging tables.
> Does NOT download data. Does NOT modify source parquet files.
> Raw activity factors remain blocked until true exposure controls are loaded.

---

## 1. Required Future Datasets

| Dataset | Source API | Frequency | Suggested File | Columns |
|---------|-----------|-----------|---------------|---------|
{chr(10).join(schema_rows)}

## 2. Staging Directory

| Item | Value |
|------|-------|
| Path | {r['staging']['path']} |
| Status | {staging_status} |

## 3. Join Policy

{r['join_policy']}

## 4. Source Files Protected (must not be modified)

{chr(10).join('- ' + f for f in r['source_files_protected'])}

## 5. Download Steps

{chr(10).join(r['download_steps'])}

## 6. Schema Validation

| Item | Value |
|------|-------|
| Valid | {'Yes' if r['schema_validation']['valid'] else 'No'} |
| Errors | {len(r['schema_validation']['errors'])} |

## 7. Current Blockers

| Gate | Status |
|------|--------|
| data_contract_ready | {contract_ready} |
| download_performed | {dl_performed} |
| neutralization_ready | {neut_ready} |
| Raw activity promotion | blocked |
| light_model_scout | blocked |
| GP | {r['gp_status']} |
| Phase 2 | {r['phase2_status']} |

## 8. Generated Files

| File | Location |
|------|----------|
| JSON | report/exposure_controls_data_contract.json |
| Report | report/exposure_controls_data_contract.md |
| Report (analysis) | analysis/exposure_controls_data_contract.md |
| Script | diagnostics/exposure_controls_data_contract.py |
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        path = os.path.join(d, "exposure_controls_data_contract.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)

    print(f"data_contract_ready: {contract_ready}")
    print(f"download_performed: {dl_performed}")
    print(f"neutralization_ready: {neut_ready}")
    print(f"Schemas defined: {len(r['schemas'])}")
    print(f"Reports written to {REPORT_DIR}/ and {ANALYSIS_DIR}/")


def main():
    result = compute_all()
    generate_report(result)


if __name__ == "__main__":
    main()
