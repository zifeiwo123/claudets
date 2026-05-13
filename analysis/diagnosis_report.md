# claudets diagnosis report: why 50 iterations found no positive alpha

**Date**: 2026-05-13
**Commit**: 887ee89

---

## Reproduced

| Item | Status |
|------|--------|
| qfq forward-adjusted prices | Pipeline supported |
| Real weekly trading dates | Implemented (W-FRI anchor) |
| Daily-derived feature snapshots | Implemented (8 features) |
| Train/val/test split | 2023-2024 / 2024-2025 / 2025+ |
| Fixed universe (top 400 by train-period volume) | Implemented |
| Expression-tree genetic programming | Implemented |
| Constrained search (no raw OHLCV/volume/amount) | Implemented |
| Validation IC direction flipping | Implemented |
| Turnover cost subtraction | Implemented |
| Forward vol timing (no post-hoc clip) | Implemented |
| ts_corr vectorization | Implemented |
| Stagnation detection | Implemented |
| Incremental summary save | Implemented |

## Partial

| Item | Status |
|------|--------|
| Market-cap-tiered slippage | Model exists, not wired to backtest |
| Long-short portfolio | Implemented |
| Long-only portfolio | Not yet |
| Industry/size neutralization | Not yet |
| Final holdout validation | Not yet |

---

## Experimental Results

### Experiment 1: Original search space (before 74cbbd8)

- **Iterations**: 166 (35-200, interrupted)
- **Sharpe**: All negative, best -0.64, mean -1.66
- **Root cause**: Factor pool collapsed to ts_max(volume), rank(amount) etc. Old constraints only blocked scale(volume) identity transforms, not wrapped expressions

### Experiment 2: Daily-feature constraints + stagnation fix (887ee89)

- **Iterations**: 50 (1-50, clean run)
- **Sharpe**: All negative, best -1.46, mean -2.39
- **Search space**: Clean. All factors based on 8 daily-derived fields
- **Evolution**: Terminates in 1-3 gens, no more stagnation
- **Speed**: ~20s/iteration (was ~70s)

### Manual IC verification

Simple factors on fixed universe (train-period volume top 400):

| Factor | Val IC_mean | Val IC_IR | Test IC_mean | Test IC_IR |
|--------|-------------|-----------|-------------|------------|
| 1w reversal (-ret_1w) | +0.002 | +0.01 | +0.044 | +0.25 |
| 4w reversal (-ret_4w) | +0.035 | +0.18 | +0.043 | +0.26 |
| Low vol (-vol_4w) | +0.027 | +0.13 | +0.026 | +0.17 |
| Small size (-volume) | **+0.083** | **+0.68** | **+0.047** | **+0.46** |
| Low amplitude (-amplitude) | +0.045 | +0.19 | +0.043 | +0.23 |

---

## Root Cause Analysis

### Signals exist, but too weak

All simple factors have the CORRECT IC sign (reversal, low vol, small-size premium). Direction is consistent between validation and test. **The search space is clean, evolution direction is correct, research methodology is sound.**

The problem: **IC_std is 3-5x larger than IC_mean**. For the strongest single factor (small-size, val IC=+0.083, IC_std=0.121):



This is for the **single strongest factor**. The actual portfolio blends 20+ factors, most with IC_mean < 0.03, producing negative net returns.

### Three structural causes

**1. Universe selection is anti-alpha**



In A-shares, true predictive alpha (short-term reversal, idiosyncratic vol, fund flows) is stronger in mid/small caps. Selecting top 400 by volume systematically excludes alpha-rich stocks. What is left are institutional heavyweights covered by every quant desk.

**2. Weekly frequency falls in the factor dead zone**



Manual verification shows 1-week reversal IC is near zero in validation (+0.002). 4-week reversal barely registers (+0.035). Weekly frequency is exactly where short-term reversal fades and medium-term momentum has not yet kicked in.

**3. Cost structure is unworkable**



For factors with IC_mean = 0.04-0.08, annualized 20.8% cost is nearly impossible to overcome. Even the strongest volume factor (IC=0.08) yields theoretical annual gross ~33%, net ~12% after costs — but 25% of weeks the factor points wrong, making realized returns far noisier.

### Not a bug — economics

The engineering pipeline is correct. The problem is in research design parameters — the combination of universe, frequency, and cost produces negative expectancy.

---

## Solutions

### Short-term (small changes, immediate impact)

**A. Change universe construction — use mid-cap stocks**

Exclude top 20% (largest, lowest alpha) and bottom 20% (too illiquid). Use middle 60% or 400 stocks from quartile 2-3.

**B. Add more daily-derived features**

The current 8 features miss key A-share signals:

| New feature | Computation | Captures |
|-------------|-------------|----------|
| d_gap_ret_5d | Sum of daily gap returns (open/prev_close-1) | Overnight information |
| d_turnover_20d | 20d mean turnover rate | True liquidity |
| d_ret_skew_20d | 20d daily return skewness | Asymmetric moves |
| d_max_ret_20d | 20d maximum daily return | MAX effect (lottery preference) |
| d_idio_vol_20d | 20d idiosyncratic volatility | Residual vol after market |
| d_close_position_20d | 20d mean of (close-low)/(high-low) | Price position within range |

**C. Tighten factor selection — IC_IR > 0.3 threshold**

Current IC_IR > 0.05 is too loose. Noise factors dilute the few meaningful ones.

### Medium-term (moderate changes)

**D. Implement long-only portfolio**

Test period: CSI 300 +20.8%, ChiNext +75.3%. Shorting beta is the dominant loss source. Long-only carries natural beta exposure — Sharpe typically better than long-short in upward-trending markets.

**E. Rolling universe (no look-ahead)**

Current universe is fixed from 2023-2024. Rebuild quarterly using only t-1 information.

**F. Reduce rebalancing frequency or use tiered slippage**

Bi-weekly or monthly rebalancing reduces turnover costs. Market-cap-tiered slippage model already exists but not wired in.

### Long-term (infrastructure needed)

**G. Industry neutralization** — A-share sector rotation is extremely strong

**H. Expanded search space** — EMA, MACD-style nonlinear ops; factor interactions; north-bound flows, margin data

---

## Risks & Limitations

1. Above proposals are untested — each needs experimental validation
2. A-share regime shifts may break train/val patterns in test
3. Cost model simplified (no limit-up/down constraints)
4. If there is an undiscovered data bug (e.g., return misalignment), above solutions are moot

---

## Next Steps

1. Implement A (mid-cap universe) + C (IC_IR > 0.3 filter), test 10 iterations
2. Implement B (6 new daily features), regenerate feature file
3. Implement D (long-only), output alongside long-short
4. If still no positive Sharpe: audit data quality — compare Tushare prices against public sources tick by tick
