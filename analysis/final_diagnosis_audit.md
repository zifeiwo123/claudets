# final diagnosis audit: 口径核查与 Phase 1 前置审查

**Date**: 2026-05-13
**Status**: Audit complete. Phase 1 must NOT start until these issues are addressed.
**References**: analysis/diagnosis_report.md | analysis/diagnosis_followup.md | analysis/final_diagnosis_report.md

---

## 1. Why this audit is needed

The current diagnosis reports have reached important directional conclusions (long-only > long-short, mid-cap > large-cap). However, before executing Phase 1, several critical issues must be resolved:

1. A **contradiction** in the long-short Sharpe numbers for `-volume` (+0.91 vs -0.71)
2. The **high absolute Sharpe** of long-only may be primarily beta, not alpha
3. The **universe comparisons** may have look-ahead bias
4. The **test period** has already been used for direction selection
5. The **Phase 1 acceptance criteria** are too weak (absolute Sharpe >= 0.5)
6. The claim that "GP is not the problem" may be overstated

This audit addresses each of these before any code changes are made.

---

## 2. Long-short consistency check: resolving the +0.91 vs -0.71 contradiction

### 2.1 The discrepancy

| Source | `-volume` LS Net Sharpe | Period |
|--------|------------------------|--------|
| Experiment A (strategy decomposition) | **+0.91** | Full (2023-2026) |
| Experiment B (single factor table) | **-0.71** | Test only (2025-07+) |
| Experiment D (IC_IR grid) | **-0.71** | Test only (2025-07+) |

### 2.2 Root cause: different time periods

Running `-volume` long-short identically across each period:

| Period | Net Sharpe | Gross Sharpe | Net Ann.Ret | Turnover | Weeks |
|--------|-----------|-------------|-------------|----------|-------|
| Full (2023-2026) | **+0.91** | +1.31 | +14.9% | 27% | 142 |
| Train (2023-2024) | **+1.17** | +1.56 | +22.5% | 29% | 64 |
| Val (2024-2025) | **+1.61** | +2.09 | +24.6% | 27% | 43 |
| Test (2025-07+) | **-0.71** | -0.25 | -8.2% | 27% | 35 |

**Both numbers are correct.** The +0.91 is the full-sample aggregate; the -0.71 is the test-period result. The full-sample number is misleading because it is dominated by earlier periods (train + val = 107 weeks vs test = 35 weeks).

### 2.3 What this means

- **`-volume` long-short was genuinely profitable in 2023-2025, but failed in 2025-07+.**
- The failure is period-specific, likely because 2025-07+ is a strong bull market.
- The same function, universe, and parameters were used — the only difference is the time window.
- **The original conclusion "long-short is the problem" overgeneralizes** — long-short worked well for 2.5 years before failing in the test period. The problem is more specifically "long-short in the 2025-07+ bull market is the problem."

### 2.4 Corrected conclusion

| Statement | Correct? |
|-----------|----------|
| "Long-short spread is positive" | TRUE for full period |
| "Long-short works in normal markets" | TRUE for train + val |
| "Long-short fails in the current bull market" | TRUE for test |
| "Long-short is universally the problem" | OVERSTATED — it's period-dependent |

---

## 3. Long-only alpha metrics: how much is beta?

### 3.1 Key finding: most long-only Sharpe comes from beta

Test period, long-only top 50:

| Universe | Factor | Abs Sharpe | **Excess vs EW** | **IR vs EW** |
|----------|--------|-----------|-------------------|-------------|
| U1 top400 vol | -ret_4w | 2.00 | **-2.4%** | **-0.24** |
| U1 top400 vol | -volume | 1.96 | **-4.6%** | **-0.75** |
| U2 amount mid | -volume | 3.19 | **+7.3%** | **+1.16** |
| U3 vol*close mid | -volume | 3.43 | **+9.6%** | **+1.41** |
| U4 liquidity filt | -volume | 3.55 | **-6.2%** | **-1.05** |

**Out of 20 LO50 combinations (4 universes x 5 factors), only 2 have positive excess vs universe equal-weight.** Both are `-volume` on U2/U3.

### 3.2 LO100 tells the same story

Test period, long-only top 100:

| Universe | Factor | Abs Sharpe | **Excess vs EW** | **IR vs EW** |
|----------|--------|-----------|-------------------|-------------|
| U2 amount mid | -volume | 2.94 | **+3.0%** | **+0.53** |
| U3 vol*close mid | -volume | 2.83 | **+1.3%** | **+0.22** |

Only 2/20 LO100 combos have positive excess. Same two combos as LO50.

### 3.3 By period: where does the alpha actually come from?

`-volume` LO50 excess vs universe EW across ALL periods:

| Universe | Train Excess | Val Excess | Test Excess |
|----------|-------------|-----------|-------------|
| U1 top400 vol | +2.9% | **+10.9%** | **-4.6%** |
| U2 amount mid | -5.8% | **+11.1%** | **+7.3%** |
| U3 vol*close mid | -4.7% | **+11.5%** | **+9.6%** |
| U4 liquidity filt | **-18.4%** | -1.9% | **-6.2%** |

**The val period (2024-2025) shows consistently strong alpha across all universes, but this does NOT replicate in the test period.** Only U2/U3 maintain positive excess in test. U1 and U4 revert to negative.

### 3.4 Conclusion on alpha

1. **Long-only absolute Sharpe is high mainly due to universe beta.** The universe EW itself returned +25% annualized in the test period.
2. **Only `-volume` on U2/U3 shows consistent positive excess across val AND test.** This is the only signal worth pursuing.
3. **`-ret_4w` has high absolute Sharpe (2.0) but NEGATIVE excess (-2.4%).** It is co-moving with the universe, not adding alpha.
4. **U4 (liquidity filtered) has the worst alpha metrics** despite the highest absolute Sharpe — it amplifies beta but destroys alpha.
5. **Val period excess is systematically inflated vs test period.** Using val-period metrics to select factors/universes would be overfitting.

---

## 4. Universe construction audit

### 4.1 Construction summary

| Universe | Field | Period | Train-only | Test info | Stocks |
|----------|-------|--------|-----------|-----------|--------|
| U1: top400 volume | mean(volume) | 2023-2024 | Yes | None | 400 |
| U2: amount mid 60% | mean(amount) | 2023-2024 | Yes | None | 400 |
| U3: vol*close mid 60% | mean(vol*close) | 2023-2024 | Yes | None | 400 |
| U4: liquidity filtered | n_days>=40, amt>p5, close>2 | 2023-2024 | Yes | None | 400 |

**All four universes use only train-period (2023-2024) information. No look-ahead bias found.**

### 4.2 Terminology correction

The original report called U2/U3/U4 "mid-cap" universes. This is incorrect because:

- `total_mv` (total market cap) and `circ_mv` (circulating market cap) fields are **not available** in current data
- `amount` = daily turnover in CNY (correlated with but not equal to market cap)
- `volume * close` = proxy for total trading value (also a liquidity proxy, not a size proxy)
- `n_days`, `close > 2` = listing age and price filters

**Correct terminology**: These are "middle trading activity" or "middle liquidity" universes, NOT "mid-cap" universes. They select stocks with moderate trading volume/amount, which may be correlated with mid-cap but is not the same thing.

### 4.3 U4 concern

U4 applies three filters (n_days>=40, amount > 5th percentile, close > 2 CNY). While all use train-only data, the combination of filters creates a sample that:
- Has the worst alpha metrics of all four universes
- Shows highly negative train-period excess (-18.4%)
- Has the highest absolute Sharpe due to survivorship-like beta amplification

**Recommendation**: Drop U4. Focus on U2 or U3.

---

## 5. Test period contamination

### 5.1 How the test period was used

The current diagnosis has already used the test period (2025-07+) for:

1. Deciding that long-only > long-short
2. Selecting U2/U3 as the best universes
3. Identifying `-ret_4w` and `-volume` as the best factors
4. Recommending IC_IR >= 0.20 threshold
5. Proposing Phase 1 acceptance criteria

**The 2025-07+ period can no longer be treated as a clean final holdout.** Any subsequent Phase 1 results on this same period are partially in-sample.

### 5.2 Proposed new validation framework

**Option A: Walk-forward across sub-periods**

| Train | Validate |
|-------|----------|
| 2023H1 | 2023H2 |
| 2023 | 2024H1 |
| 2023-2024H1 | 2024H2 |
| 2023-2024 | 2025H1 |
| 2023-2025H1 | 2025H2 |

This tests strategy stability across multiple market regimes. Phase 1 must pass in at least 3 of 5 walk-forward windows.

**Option B: Final holdout (simpler)**

| Role | Period |
|------|--------|
| Development (train + val) | 2023-01 to 2025-06 |
| Selection (GP, factor choice, universe choice) | Within development, using walk-forward |
| Final holdout (untouched) | 2026-01 onward |

The 2025-07 to 2025-12 period has already been contaminated and should be folded into the development period.

### 5.3 What data is available

The most recent data extends to 2026-05-12. With Option B:
- Development: 2023-01 to 2025-12 (3 years)
- Final holdout: 2026-01 to 2026-05 (5 months, ~22 weeks)

This holdout is short but sufficient for a preliminary out-of-sample check. It will grow over time.

---

## 6. Revised Phase 1 acceptance criteria

### 6.1 Original criteria (TOO WEAK)

```text
Long-only portfolio achieves positive Sharpe >= 0.5 in test period.
```

This can be satisfied by riding universe beta alone. The universe EW itself has Sharpe well above 0.5 in the test period.

### 6.2 Revised criteria

Phase 1 is passed only when ALL of the following are met:

1. **Positive excess vs universe equal-weight** in at least 2 of 3 recent walk-forward windows (e.g., 2024H2, 2025H1, 2025H2 for development; 2026H1 for holdout if available)
2. **Information ratio vs universe EW > 0.3** (not just positive, but reliably so)
3. **Maximum relative drawdown vs universe EW < 10%** (alpha drawdown, not beta drawdown)
4. **Weekly excess win rate > 50%** (more than half the weeks beat the universe)
5. **Not exclusively driven by the 2024-2025 val period** — must show stability
6. **Results must report BOTH absolute AND excess returns** — never report absolute Sharpe without the excess vs universe EW alongside it
7. **Turnover and cost must be reported** — annualized cost estimate
8. **Acknowledge known concentration risks** — sector, liquidity, size tilts must be flagged even if not formally neutralized

### 6.3 What "passing" Phase 1 means

Passing Phase 1 does NOT mean "this is a viable strategy." It means:
- The signal has demonstrated alpha beyond universe beta
- It is stable enough across sub-periods to warrant further development
- Phase 2 (feature expansion, GP) can begin

---

## 7. Revised conclusion on GP

### 7.1 Original claim (OVERSTATED)

```text
GP is not the problem. The backtest portfolio structure is.
```

### 7.2 Revised claim

```text
GP has not yet demonstrated incremental value over simple baseline factors.
The 50-iteration GP run produced no factor that outperforms -ret_4w or -volume
in either IC stability or portfolio returns.
```

Evidence:
- The top GP factors had val IC_IR up to 1.27 (iter 204) but produced NEGATIVE test-period returns
- The simple manual factors (-ret_4w, -volume) outperform every GP-produced factor in test
- GP was evaluated in a long-short framework where even good factors produce negative net returns
- We have not yet tested whether GP factors would work in a long-only setting — but there is no reason to believe they would outperform the simple baselines

### 7.3 When to re-enable GP

GP should only be re-enabled after:
1. Simple baseline factors pass Phase 1 acceptance criteria
2. The simple baseline's performance is documented and stable across walk-forward windows
3. Any new GP-produced factor must be benchmarked against the simple baseline — if it cannot outperform `-volume` or `-ret_4w`, it should not enter the portfolio

---

## 8. Summary of corrections needed in final_diagnosis_report.md

| Original Statement | Correction |
|-------------------|------------|
| "Long-short structure is the primary failure source" | "Long-short failed specifically in the 2025-07+ bull market; it was profitable in 2023-2025" |
| "Long leg is profitable (+41.7%)" | True, but full-period; test-period long leg was +18.7% |
| "Mid-cap universes improve Sharpe to 3.4-3.6" | True for absolute Sharpe, but excess vs EW is only +0.10 annualized — mostly beta |
| "Cost is manageable (5.6% annualized)" | True, but irrelevant since alpha (excess vs EW) is near zero for most factors |
| "GP is not the problem" | Overstated — GP has not proven incremental value; rephrase as above |
| U2/U3/U4 are "mid-cap universes" | These are middle-trading-activity universes; total_mv and circ_mv are unavailable |
| Phase 1: "positive Sharpe >= 0.5" | Replace with excess vs universe EW criteria above |

---

## 9. Generated files

| File | Description |
|------|-------------|
| report/final_diagnosis_audit.md | This report |
| report/ls_consistency_check.parquet | -volume LS per period |
| report/long_only_alpha_metrics.parquet | Absolute + excess metrics for all factor/universe/period combos |
| report/universe_construction_audit.csv | Universe construction verification |

---

## 10. Next step

**Do not execute Phase 1 yet.**

Instead:
1. Fix the overstatements in analysis/final_diagnosis_report.md per Section 8 above
2. Implement the walk-forward framework from Section 5.2
3. Re-run long-only tests on walk-forward windows using ONLY `-volume` and `-ret_4w` (the only factors with any alpha signal)
4. Only U2 and U3 universes should be carried forward (drop U1, drop U4)
5. Report BOTH absolute AND excess metrics in all future reports
6. GP remains paused until simple baselines pass walk-forward
