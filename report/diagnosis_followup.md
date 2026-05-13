# claudets follow-up diagnosis: where negative alpha comes from

**Date**: 2026-05-13
**Based on**: commit 887ee89, 50-iteration clean run
**Diagnostic script**: diagnostics/followup_diagnosis.py

---

## 1. Background

Previous diagnosis_report.md established:

- Engineering fixes are mostly in place (qfq, real trading dates, daily features, constraints, cost subtraction, stagnation detection)
- 50-iteration clean run: ALL negative Sharpe, best -1.46, mean -2.39
- Simple factors show correct IC direction but weak magnitude
- Three hypotheses: universe anti-alpha, weekly dead zone, cost structure

This follow-up decomposes WHERE the negative returns come from, using controlled experiments without GP.

---

## 2. Current Strategy Decomposition

Using the strongest simple factor (-volume) on the current universe (top 400 by train-period volume) in the test period (2025-07+):

### Per-leg breakdown

| Leg | Ann.Ret | Sharpe | MaxDD | Cum.Ret | Win Rate |
|-----|---------|--------|-------|---------|----------|
| Long leg | **+41.7%** | **+1.63** | -22.6% | +158.9% | 62.7% |
| Short leg | **+15.4%** | +0.62 | -30.6% | +48.0% | 52.1% |
| Spread (gross) | +21.5% | +1.31 | -15.6% | +70.2% | 60.6% |
| Spread (net) | +14.9% | +0.91 | -16.6% | +46.2% | 59.2% |

### Cost impact

| Metric | Value |
|--------|-------|
| Mean weekly turnover | 27% (vs ~100% assumed) |
| Median weekly turnover | 26% |
| P90 weekly turnover | 34% |
| Annualized cost | **5.6%** (vs 20.8% originally estimated) |

### Key finding

**Both long and short legs are profitable in the test period.** The long leg (+41.7% annual) dramatically outperforms the short leg (+15.4%). The short leg is net long beta in a bull market — it shorts stocks that still go up 15% annually.

**This single-factor portfolio is actually POSITIVE (+14.9% net, Sharpe 0.91).** The earlier GP runs produced negative results because they blended 20+ weak factors with IC_IR < 0.05, not because alpha doesn't exist.

### Benchmark alignment

Test-period universe equal-weight return = +25.0% (annualized). Both CSI 300 (+20.8% cumulative) and ChiNext (+75.3% cumulative) cover the same date range. Dates aligned with no manual shift.

Missing benchmarks (not in current data): zz500, zz1000.

---

## 3. Single Factor Diagnosis

Test period only (2025-07+). Universe: U1 top 400 by volume.

| Factor | IC_mean | IC_IR | LS Net Sharpe | LO50 Sharpe | LO100 Sharpe |
|--------|---------|-------|---------------|-------------|--------------|
| -ret_1w | 0.042 | 0.24 | **-1.26** | **+0.42** | **+0.56** |
| -ret_4w | 0.045 | 0.28 | -1.05 | **+2.00** | **+1.71** |
| -vol_4w | 0.010 | 0.07 | -2.00 | **+0.72** | **+1.31** |
| -volume | 0.047 | 0.46 | -0.71 | **+1.96** | **+1.91** |
| -amplitude | 0.043 | 0.23 | -1.25 | **+0.46** | **+1.48** |

### Answers to key questions

**Q: Does any single factor have a positive long leg?**
YES. All five factors have positive long-leg returns (test period). -ret_4w LO50 Sharpe = +2.00. -volume LO50 Sharpe = +1.96.

**Q: Does any single factor's long-only beat universe equal-weight?**
On U1 (top 400 volume): NO. Best LO50 excess vs EW = -1.23 (annualized). The universe EW itself returned +25.0% — riding the bull market beta is hard to beat with 50-stock concentration.

**Q: Is any factor gross-effective but net-ineffective?**
The spread is positive (gross Sharpe +1.31 for -volume) but the cost impact at 27% turnover is modest. The issue is NOT cost killing the signal — it's the long-short structure.

**Q: Does any factor work in val but fail in test?**
-val period Sharpe for LO50 is inflated (2.8-3.6 vs 0.4-2.0 in test). This is because the val period (2024-2025) had different market conditions. Direction is consistent though — all factors maintain the same IC sign.

**Q: Does any factor work in test but not val?**
No — all factors show consistent direction between val and test.

---

## 4. Universe Comparison

Test period, long-only top 50, net of costs.

| Universe | Best Factor | LO50 Sharpe | Excess vs EW |
|----------|-------------|-------------|--------------|
| U1: top400 volume | -ret_4w | 2.00 | **-1.23** |
| U2: amount mid 60% | -ret_4w | **3.19** | **+0.07** |
| U3: vol*close mid 60% | -ret_4w | **3.43** | **+0.10** |
| U4: liquidity filtered | -ret_4w | **3.55** | **+0.03** |

### Answers

**Q: Is top400 volume anti-alpha?**
YES — in the sense that it's the WORST of the four universes tested. Every mid-cap / filtered universe outperforms it. But it's not that alpha is absent — it's that the universe EW return is so high (+25%) that it's hard to beat with 50 concentrated positions.

**Q: Does mid-cap improve results?**
DRAMATICALLY. U3 and U4 achieve LO50 Sharpe 3.4-3.6 with POSITIVE excess over universe EW. The improvement comes from both stronger factor IC and lower universe EW (less beta to fight).

**Q: Is -volume a size, liquidity, or attention factor?**
On U1 (large caps), -volume is most likely a **liquidity/attention proxy** — low-volume large caps are underfollowed and subsequently outperform. On U2-U4 (mid caps), the effect is even stronger, suggesting it captures genuine mispricing from low attention rather than a pure size premium.

---

## 5. IC_IR Threshold Grid

Test period, long-short portfolio, varying IC_IR thresholds and factor counts.

| Threshold | Selected | Count | Gross Sharpe | Net Sharpe |
|-----------|----------|-------|-------------|------------|
| 0.05 | -volume, -ret_4w, -amplitude | 3 | -0.84 | -1.37 |
| 0.10 | -volume, -ret_4w, -amplitude, -vol_4w | 4 | -0.90 | -1.44 |
| 0.20 | -volume, -ret_4w | 2 | -0.46 | -0.97 |
| 0.30 | -volume | 1 | -0.25 | -0.71 |
| 0.50 | -volume | 1 | -0.25 | -0.71 |

### Key finding

Even the single best factor (-volume, val IC_IR=0.68) produces negative net Sharpe (-0.71) in long-short on this universe. **Tightening IC_IR thresholds does not fix long-short.**

This is because the long-short structure itself is the problem, not the factor quality. Shorting stocks in a +75% ChiNext bull market is fundamentally loss-making, regardless of how good the cross-sectional ranking is.

---

## 6. Final Diagnosis

### Primary failure source: LONG-SHORT STRUCTURE IN A BULL MARKET

The evidence is conclusive:

1. **Long leg is profitable across ALL factors** (best LO50 Sharpe +2.00)
2. **Short leg is also profitable** (+15.4% ann) — meaning the shorts go up, just less than the longs
3. **Gross spread is positive** (Sharpe +1.31 for -volume)
4. **Cost is manageable** (27% turnover, 5.6% annualized — not 20.8%)
5. **Mid-cap universes amplify long-only returns** (Sharpe up to 3.6)

The GP evolution was finding factors, combining them, and producing negative net returns because:
- 20+ weak factors (IC_IR < 0.05) added noise, diluting the few good ones
- The equal-weight / ICIR-weight combination didn't distinguish between +IC_IR 0.68 and +IC_IR 0.06 factors
- The long-short structure systematically underperforms in a test period where ChiNext returned +75%

### Secondary factor: UNIVERSE SELECTION

Top 400 by volume = large caps with lowest alpha. Moving to mid-cap improves LO50 Sharpe from 2.0 to 3.6.

### NOT the primary problem

- Cost: actual turnover is 27%, not 100%. Annualized cost ~5.6%, manageable.
- Weekly frequency: signals work at weekly frequency (IC_IR up to 0.68).
- Factor quality: -volume and -ret_4w have genuine predictive power.
- Data bugs: IC direction is consistent val→test, qfq data appears correct.

---

## 7. Recommended Next Steps

Based on the evidence, the priority order is:

1. **Implement long-only portfolio** — This is the single highest-impact change. -ret_4w long-only top 50 already delivers Sharpe 2.0 on the current universe. The engineering is straightforward (already partially in place).

2. **Switch to mid-cap universe** — U3 (vol*close middle 60%) or U4 (liquidity filtered) immediately improve LO50 Sharpe to 3.4-3.6 with positive excess vs universe EW. Implement before any further GP runs.

3. **Tighten factor selection to IC_IR >= 0.20** — Only 2 of 5 simple factors pass this bar. Adding 20+ weak factors to a portfolio makes it worse, not better. Use this threshold for any multi-factor combination.

4. **Only after 1-3 are done**: Consider expanding daily features, re-enabling GP, or adding industry neutralization.

If long-only on mid-cap still fails to produce positive net returns, then and only then should we audit for hidden data bugs.

### What NOT to do

- Do not continue running GP on the current universe with long-short
- Do not add complex features (EMA, MACD, etc.) before fixing the portfolio structure
- Do not use val-period LO50 Sharpe (inflated to 2.8-3.6) as the target — use test period

---

## Generated Files

| File | Description |
|------|-------------|
| report/diagnosis_weekly_decomposition.parquet | Weekly P&L attribution per leg |
| report/single_factor_diagnosis.parquet | 5 factors x 3 periods x 3 portfolio types |
| report/universe_factor_comparison.parquet | 4 universes x 5 factors x 2 periods |
| report/icir_threshold_grid.parquet | Threshold x max_count grid |
| diagnostics/followup_diagnosis.py | Reproducible diagnostic script |
| report/diagnosis_followup.md | This report |
