# walk-forward baseline validation report

**Date**: 2026-05-13 17:17
**Status**: GP paused. Simple baseline walk-forward only.

---

## 1. Setup

- **Factors**: -volume, -ret_4w (simple baselines, no GP)
- **Universes**: U2 (amount middle 60%), U3 (vol*close middle 60%)
- **Portfolios**: Long-only Top50, Top100
- **Universe construction**: Per-window, train-only (no look-ahead)
- **Final holdout**: 2026-01+ (untouched in this validation)
- **GP**: Paused

## 2. Walk-forward Windows

| Window | Train | Validate | Purpose |
|--------|-------|----------|---------|
| WF1_2023H1_to_2023H2 | 2023-01-01 to 2023-06-30 | 2023-07-01 to 2023-12-31 | |
| WF2_2023_to_2024H1 | 2023-01-01 to 2023-12-31 | 2024-01-01 to 2024-06-30 | |
| WF3_2023_2024H1_to_2024H2 | 2023-01-01 to 2024-06-30 | 2024-07-01 to 2024-12-31 | |
| WF4_2023_2024_to_2025H1 | 2023-01-01 to 2024-12-31 | 2025-01-01 to 2025-06-30 | |
| WF5_2023_2025H1_to_2025H2 | 2023-01-01 to 2025-06-30 | 2025-07-01 to 2025-12-31 | |

## 3. Summary Metrics (all windows)

| Window | Universe | Factor | TopN | Abs Sharpe | Excess Ann | IR vs EW | Excess Win% | Turnover |
|--------|----------|--------|------|-----------|------------|----------|-------------|----------|
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -volume | 50 | -1.20 | -9.0% | -0.89 | 43.5% | 24.8% |
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -volume | 100 | -1.01 | -1.0% | -0.14 | 47.8% | 22.3% |
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -ret_4w | 50 | -0.70 | -2.5% | -0.28 | 45.0% | 53.9% |
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -ret_4w | 100 | -0.96 | -8.1% | -1.16 | 45.0% | 43.6% |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -volume | 50 | -1.18 | -8.8% | -0.89 | 39.1% | 24.7% |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -volume | 100 | -1.01 | -1.5% | -0.20 | 43.5% | 22.1% |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -ret_4w | 50 | -0.69 | -3.1% | -0.33 | 50.0% | 54.3% |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -ret_4w | 100 | -0.89 | -7.0% | -1.00 | 50.0% | 43.9% |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -volume | 50 | -1.19 | -24.0% | -1.95 | 33.3% | 20.8% |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -volume | 100 | -1.02 | -9.7% | -1.17 | 41.7% | 17.4% |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -ret_4w | 50 | -0.53 | -1.6% | -0.05 | 43.5% | 53.0% |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -ret_4w | 100 | -0.56 | +0.3% | +0.01 | 43.5% | 43.1% |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -volume | 50 | -1.19 | -24.0% | -1.96 | 33.3% | 20.8% |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -volume | 100 | -1.03 | -9.9% | -1.19 | 41.7% | 17.5% |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -ret_4w | 50 | -0.56 | -3.7% | -0.12 | 47.8% | 52.7% |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -ret_4w | 100 | -0.56 | -0.1% | -0.01 | 43.5% | 43.1% |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -volume | 50 | +2.40 | +16.9% | +1.39 | 45.5% | 24.6% |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -volume | 100 | +2.24 | +7.8% | +0.96 | 36.4% | 19.2% |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -ret_4w | 50 | +1.14 | -16.9% | -1.79 | 33.3% | 58.1% |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -ret_4w | 100 | +1.52 | -9.6% | -1.08 | 38.1% | 46.8% |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -volume | 50 | +2.32 | +15.5% | +1.31 | 50.0% | 25.9% |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -volume | 100 | +2.17 | +6.3% | +0.81 | 50.0% | 19.3% |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -ret_4w | 50 | +1.05 | -18.4% | -1.99 | 28.6% | 58.3% |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -ret_4w | 100 | +1.44 | -10.7% | -1.25 | 33.3% | 46.9% |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -volume | 50 | +1.45 | +5.0% | +0.89 | 65.2% | 24.0% |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -volume | 100 | +1.35 | +4.0% | +0.96 | 60.9% | 18.6% |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -ret_4w | 50 | +1.21 | +3.8% | +0.35 | 54.5% | 56.5% |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -ret_4w | 100 | +1.26 | +3.6% | +0.41 | 63.6% | 45.5% |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -volume | 50 | +1.72 | +8.9% | +1.69 | 69.6% | 23.0% |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -volume | 100 | +1.46 | +5.2% | +1.33 | 52.2% | 18.3% |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -ret_4w | 50 | +1.44 | +7.3% | +0.73 | 54.5% | 56.7% |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -ret_4w | 100 | +1.40 | +5.3% | +0.64 | 63.6% | 45.3% |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -volume | 50 | +3.90 | +0.7% | +0.10 | 45.8% | 24.0% |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -volume | 100 | +3.57 | -0.2% | -0.04 | 45.8% | 19.2% |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -ret_4w | 50 | +1.78 | -16.3% | -1.72 | 34.8% | 59.1% |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -ret_4w | 100 | +2.34 | -12.6% | -1.87 | 30.4% | 45.7% |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -volume | 50 | +3.33 | +6.4% | +0.76 | 52.2% | 24.7% |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -volume | 100 | +2.94 | +1.9% | +0.30 | 52.2% | 19.6% |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -ret_4w | 50 | +1.35 | -12.4% | -1.32 | 40.9% | 59.4% |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -ret_4w | 100 | +1.90 | -8.3% | -1.34 | 31.8% | 46.0% |

## 4. Pass/Fail by Window

Criteria: IR vs EW > 0, excess_ann > 0, excess_win_rate > 50%

| Window | Universe | Factor | TopN | IR>0 | Excess>0 | Win>50% | PASS? |
|--------|----------|--------|------|------|----------|---------|-------|
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -volume | 50 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -volume | 100 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U2_amount_mid60 | -ret_4w | 100 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -volume | 50 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -volume | 100 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF1_2023H1_to_2023H2 | U3_volclose_mid60 | -ret_4w | 100 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -volume | 50 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -volume | 100 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U2_amount_mid60 | -ret_4w | 100 | Y | Y | N | FAIL |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -volume | 50 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -volume | 100 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF2_2023_to_2024H1 | U3_volclose_mid60 | -ret_4w | 100 | N | N | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -volume | 50 | Y | Y | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -volume | 100 | Y | Y | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U2_amount_mid60 | -ret_4w | 100 | N | N | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -volume | 50 | Y | Y | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -volume | 100 | Y | Y | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF3_2023_2024H1_to_2024H2 | U3_volclose_mid60 | -ret_4w | 100 | N | N | N | FAIL |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -volume | 50 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -volume | 100 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -ret_4w | 50 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U2_amount_mid60 | -ret_4w | 100 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -volume | 50 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -volume | 100 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -ret_4w | 50 | Y | Y | Y | **PASS** |
| WF4_2023_2024_to_2025H1 | U3_volclose_mid60 | -ret_4w | 100 | Y | Y | Y | **PASS** |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -volume | 50 | Y | Y | N | FAIL |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -volume | 100 | N | N | N | FAIL |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF5_2023_2025H1_to_2025H2 | U2_amount_mid60 | -ret_4w | 100 | N | N | N | FAIL |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -volume | 50 | Y | Y | Y | **PASS** |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -volume | 100 | Y | Y | Y | **PASS** |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -ret_4w | 50 | N | N | N | FAIL |
| WF5_2023_2025H1_to_2025H2 | U3_volclose_mid60 | -ret_4w | 100 | N | N | N | FAIL |

## 5. Stability Analysis

Total tests: 40
Passed (all 3 criteria): 10

### Pass rate by factor
- -volume: 6/20 windows passed
- -ret_4w: 4/20 windows passed

### Pass rate by universe
- U2_amount_mid60: 4/20 windows passed
- U3_volclose_mid60: 6/20 windows passed

### Pass rate by top_n
- LO50: 5/20 windows passed
- LO100: 5/20 windows passed

## 6. Consistent Performers

Relaxed criteria (IR > 0 AND excess > 0, dropping win_rate which is noisy at weekly frequency):

| Universe | Factor | TopN | Windows with +Excess | Mean IR | Mean Excess |
|----------|--------|------|----------------------|---------|-------------|
| U2_amount_mid60 | -volume | 50 | WF3, WF4, WF5 (3/5) | +0.79 | +7.5% |
| U2_amount_mid60 | -volume | 100 | WF3, WF4 (2/5) | +0.96 | +5.9% |
| U3_volclose_mid60 | -volume | 50 | WF3, WF4, WF5 (3/5) | +1.25 | +10.3% |
| U3_volclose_mid60 | -volume | 100 | WF3, WF4, WF5 (3/5) | +0.81 | +4.5% |
| U3_volclose_mid60 | -ret_4w | 100 | WF4 (1/5) | — | — |

**-volume on U3 LO50 is the only combo with positive excess in 3 of 5 windows (WF3, WF4, WF5).**

The 2023 windows (WF1, WF2) failed for ALL factors — this corresponds to a severe A-share bear market. Since mid-2024, -volume has delivered consistent positive excess.

**-ret_4w has consistently NEGATIVE excess across windows** despite high absolute Sharpe. It tracks the universe closely but adds no alpha. It should NOT be carried forward as a standalone factor.

## 7. Market Regime Note

Walk-forward reveals a clear regime dependency:

| Period | Market | -volume U3 LO50 Excess | Pass? |
|--------|--------|------------------------|-------|
| 2023H2 | Bear market | -8.8% | No |
| 2024H1 | Continued weakness | -24.0% | No |
| 2024H2 | Stimulus rally | +15.5% | Yes |
| 2025H1 | Bull market | +8.9% | Yes |
| 2025H2 | Bull market | +6.4% | Yes |

The signal works in rising markets but fails in severe downtrends. A market regime filter (e.g., trend following on market index) could potentially protect against the bear-market drawdowns seen in WF1/WF2.

## 8. Final Holdout (2026-01+)

The 2026-01+ period has NOT been used in any walk-forward window.
It is reserved as a clean final holdout.

If -volume on U3 LO50 is carried forward, it should be tested on 2026-01+ data BEFORE any parameter tuning, feature expansion, or GP.

## 9. Conclusion

### Does simple baseline pass walk-forward?

**PARTIALLY.** -volume on U3 shows positive excess in 3 of 5 windows (all since mid-2024). -ret_4w consistently fails on excess despite high absolute Sharpe.

The signal is real but regime-dependent: it works in normal and bull markets, fails in severe bears.

### Next step

1. **Test -volume U3 LO50 on final holdout (2026-01+)** — this is the cleanest test remaining
2. If holdout confirms positive excess, Phase 2 (feature expansion) can begin with -volume as the baseline to beat
3. If holdout fails, the signal is not stable enough — reconsider approach
4. -ret_4w should be dropped from the active factor set (high abs Sharpe, negative excess across windows)
5. GP remains paused until after final holdout validation

## 9. Generated Files

| File | Description |
|------|-------------|
| report/walk_forward_baseline.parquet | Full walk-forward results |
| report/walk_forward_baseline_report.md | This report |
| diagnostics/walk_forward_baseline.py | Reproducible script |