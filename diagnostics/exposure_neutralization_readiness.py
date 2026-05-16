"""Data-availability audit for exposure neutralization.

Searches local data sources only. Does not download new data.
Reports whether market cap, industry, listing status, ST flags,
suspension, turnover rate, float shares, or similar exposure
controls exist locally. If absent, states absent clearly.

Outputs:
  report/exposure_neutralization_readiness.json
  report/exposure_neutralization_readiness.md
  analysis/exposure_neutralization_readiness.md
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

EXPOSURE_FIELDS = [
    ("total_mv", "total market cap", "Tushare daily_basic or pro_bar"),
    ("circ_mv", "circulating market cap", "Tushare daily_basic or pro_bar"),
    ("industry", "sector / industry classification", "Tushare stock_basic or index_classify"),
    ("is_st", "ST / *ST flag", "Tushare namechange or daily_basic"),
    ("suspended", "suspension flag", "Tushare suspend or trade_cal"),
    ("turnover_rate", "turnover rate (volume / float)", "Tushare daily_basic"),
    ("float_share", "circulating shares", "Tushare daily_basic"),
    ("list_date", "listing date", "Tushare stock_basic"),
    ("list_status", "listing status (L/D/P)", "Tushare stock_basic"),
]

LOCAL_DATA_FILES = [
    "data/daily_ohlcv.parquet",
    "data/weekly_ohlcv.parquet",
    "data/weekly_daily_features.parquet",
    "data/hs300_weekly.parquet",
    "data/cyb_weekly.parquet",
]


def compute_all():
    results = []
    available_cols = set()

    for fpath in LOCAL_DATA_FILES:
        if not os.path.exists(fpath):
            results.append({
                "file": fpath, "exists": False, "columns": [],
            })
            continue
        df = pd.read_parquet(fpath)
        cols = list(df.columns)
        available_cols.update(cols)
        results.append({
            "file": fpath, "exists": True,
            "rows": int(len(df)),
            "stocks": int(df["ts_code"].nunique()) if "ts_code" in cols else 0,
            "columns": cols,
        })

    # Check each exposure field
    field_audit = []
    for field, description, source_api in EXPOSURE_FIELDS:
        present = field in available_cols
        proxy = _find_proxy(field, available_cols)
        field_audit.append({
            "field": field,
            "description": description,
            "present_locally": present,
            "has_proxy": proxy is not None,
            "proxy_field": proxy,
            "proxy_note": _proxy_note(field, proxy),
            "source_api": source_api,
        })

    neutralization_ready = all(f["present_locally"] or f["has_proxy"] for f in field_audit if f["field"] in [
        "total_mv", "circ_mv", "industry", "is_st",
    ])

    def _needs_field(f):
        return f["field"] in ["total_mv", "circ_mv", "industry", "is_st"]

    missing_critical = [f for f in field_audit if _needs_field(f) and not f["present_locally"] and not f["has_proxy"]]
    existing_proxies = [f for f in field_audit if f["has_proxy"]]
    present_fields = [f for f in field_audit if f["present_locally"]]

    result = {
        "generated_at": datetime.now().isoformat(),
        "local_data_files_audited": len(LOCAL_DATA_FILES),
        "file_details": results,
        "exposure_fields": field_audit,
        "critical_fields_present": len(present_fields),
        "critical_fields_with_proxy": len(existing_proxies),
        "critical_fields_missing": len(missing_critical),
        "missing_critical_fields": [f["field"] for f in missing_critical],
        "neutralization_ready": neutralization_ready,
        "hard_blocker": not neutralization_ready,
        "recommendation": (
            "Neutralization is blocked. To proceed, download from Tushare: "
            "stock_basic (industry, list_date, list_status), daily_basic "
            "(total_mv, circ_mv, turnover_rate), and namechange (ST flags). "
            "Do not infer market cap from amount/volume."
        ) if not neutralization_ready else (
            "All critical exposure fields are available or have acceptable proxies."
        ),
        "existing_computable_proxies": [
            {"name": "n_days", "file": "weekly_ohlcv.parquet",
             "use": "proxy for listing recency and suspension (fewer days = newer or suspended)"},
            {"name": "volume * close", "file": "weekly_ohlcv.parquet",
             "use": "trading-value proxy, used in U3 universe, NOT a market cap proxy"},
            {"name": "amount", "file": "weekly_ohlcv.parquet",
             "use": "daily turnover in CNY, liquidity proxy, NOT a size proxy"},
        ],
        "gp_status": "paused",
        "phase2_status": "paused",
    }

    json_path = os.path.join(REPORT_DIR, "exposure_neutralization_readiness.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def _find_proxy(field, available_cols):
    proxies = {
        "total_mv": None,  # no acceptable proxy without actual data
        "circ_mv": None,
        "industry": None,
        "is_st": None,
        "suspended": "n_days" if "n_days" in available_cols else None,
        "turnover_rate": None,
        "float_share": None,
        "list_date": None,
        "list_status": None,
    }
    return proxies.get(field)


def _proxy_note(field, proxy):
    if field == "total_mv" and proxy is None:
        return "volume*close is NOT a market cap proxy; amount/volume should not be used as size"
    if field == "suspended" and proxy == "n_days":
        return "weeks with n_days < 3 are already filtered in preprocessor; can extend as suspension flag"
    return ""


def generate_report(result):
    r = result

    field_rows = []
    for f in r["exposure_fields"]:
        status = "PRESENT" if f["present_locally"] else ("PROXY: " + f["proxy_field"] if f["has_proxy"] else "ABSENT")
        field_rows.append(
            f"| {f['field']} | {f['description']} | {status} | {f['source_api']} |"
        )

    file_rows = []
    for f in r["file_details"]:
        if f["exists"]:
            file_rows.append(
                f"| {f['file']} | {f['rows']:,} | {f['stocks']} | "
                f"{len(f['columns'])} cols |"
            )
        else:
            file_rows.append(f"| {f['file']} | absent | - | - |")

    proxy_rows = []
    for p in r["existing_computable_proxies"]:
        proxy_rows.append(f"| {p['name']} | {p['file']} | {p['use']} |")

    ready = "true" if r["neutralization_ready"] else "false"

    report = f"""# exposure neutralization readiness

**Generated**: {r['generated_at']}
**neutralization_ready**: {ready}
**GP**: {r['gp_status']}
**Phase 2**: {r['phase2_status']}

> Audits local data only. Does not download new data.
> Final holdout untouched.

---

## 1. Local Data Files Audited

| File | Rows | Stocks | Columns |
|------|------|--------|---------|
{chr(10).join(file_rows)}

## 2. Exposure Field Audit

| Field | Description | Status | Source API |
|-------|-------------|--------|------------|
{chr(10).join(field_rows)}

## 3. Existing Computable Proxies

| Name | Source | Use |
|------|--------|-----|
{chr(10).join(proxy_rows)}

## 4. Critical Fields Missing

{len(r['missing_critical_fields'])} critical fields are absent with no acceptable proxy:

{chr(10).join('- ' + f for f in r['missing_critical_fields'])}

## 5. Recommendation

{r['recommendation']}

## 6. Decision

| Item | Value |
|------|-------|
| neutralization_ready | **{ready}** |
| Hard blocker | **{'Yes' if r['hard_blocker'] else 'No'}** |
| Raw activity promotion | blocked |
| light_model_scout | blocked |
| GP | {r['gp_status']} |
| Phase 2 | {r['phase2_status']} |

## 7. Generated Files

| File | Location |
|------|----------|
| JSON | report/exposure_neutralization_readiness.json |
| Report | report/exposure_neutralization_readiness.md |
| Report (analysis) | analysis/exposure_neutralization_readiness.md |
| Script | diagnostics/exposure_neutralization_readiness.py |
"""

    for d in [REPORT_DIR, ANALYSIS_DIR]:
        path = os.path.join(d, "exposure_neutralization_readiness.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)

    print(f"neutralization_ready: {ready}")
    print(f"Critical fields missing: {len(r['missing_critical_fields'])}")
    print(f"Reports written to {REPORT_DIR}/ and {ANALYSIS_DIR}/")


def main():
    result = compute_all()
    generate_report(result)


if __name__ == "__main__":
    main()
