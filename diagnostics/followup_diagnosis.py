"""Failure-source decomposition for claudets 50-iteration clean run.

This script reads existing data + backtest results and produces
diagnostic tables WITHOUT running new GP evolution. It outputs:

    report/diagnosis_weekly_decomposition.parquet
    report/single_factor_diagnosis.parquet
    report/universe_factor_comparison.parquet
    report/icir_threshold_grid.parquet
"""
from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import pandas as pd

# --- Paths ---
REPORT_DIR = "report"
WEEKLY_PATH = "data/weekly_ohlcv.parquet"
FEAT_PATH = "data/weekly_daily_features.parquet"
HS300_PATH = "data/hs300_weekly.parquet"
CYB_PATH = "data/cyb_weekly.parquet"

os.makedirs(REPORT_DIR, exist_ok=True)

# --- Config (mirrors autonomous_loop.py) ---
TRAIN_RANGE = ("2023-01-01", "2024-06-30")
VAL_RANGE = ("2024-07-01", "2025-06-30")
TEST_RANGE = ("2025-07-01", None)
MAX_STOCKS = 400
COST_RATE = 0.004
TOP_PCT = 0.20


def load_data():
    w = pd.read_parquet(FEAT_PATH)
    w["trade_date"] = pd.to_datetime(w["trade_date"])

    hs300 = pd.read_parquet(HS300_PATH)
    hs300["trade_date"] = pd.to_datetime(hs300["trade_date"])
    hs300 = hs300.sort_values("trade_date")
    hs300_ret = hs300.set_index("trade_date")["pct_chg"]

    cyb = pd.read_parquet(CYB_PATH)
    cyb["trade_date"] = pd.to_datetime(cyb["trade_date"])
    cyb = cyb.sort_values("trade_date")
    cyb_ret = cyb.set_index("trade_date")["pct_chg"]

    return w, hs300_ret, cyb_ret


def get_period_mask(dates, start, end=None):
    mask = dates >= start
    if end is not None:
        mask = mask & (dates <= end)
    return mask


def build_pivots(weekly, universe, fields):
    """Build pivot tables for given fields on a universe."""
    w = weekly[weekly["ts_code"].isin(universe)].copy()
    pivots = {}
    for f in fields:
        piv = w.pivot_table(index="trade_date", columns="ts_code", values=f, aggfunc="last")
        piv = piv.sort_index()
        pivots[f] = piv
    return pivots


def compute_fwd_ret(close_pivot):
    return close_pivot.shift(-1) / close_pivot - 1


def compute_simple_factor(pivots, factor_name):
    """Compute simple factor values from pivot tables. Returns DataFrame."""
    close = pivots["close"]

    if factor_name == "-ret_1w":
        ret = close.pct_change(fill_method=None)
        return -ret
    elif factor_name == "-ret_4w":
        ret = close.pct_change(4, fill_method=None)
        return -ret
    elif factor_name == "-vol_4w":
        ret = close.pct_change(fill_method=None)
        vol = ret.rolling(4, min_periods=2).std()
        return -vol
    elif factor_name == "-volume":
        vol = pivots["volume"]
        return -vol
    elif factor_name == "-amplitude":
        high = pivots["high"]
        low = pivots["low"]
        amp = (high - low) / close
        return -amp
    else:
        raise ValueError(f"Unknown factor: {factor_name}")


def compute_weekly_ic(factor_df, fwd_ret_df):
    """Cross-sectional Spearman IC per week."""
    ics = []
    for date in factor_df.index:
        if date not in fwd_ret_df.index:
            continue
        f = factor_df.loc[date].dropna()
        r = fwd_ret_df.loc[date].dropna()
        common = f.index.intersection(r.index)
        if len(common) < 10:
            continue
        ic = f[common].corr(r[common], method="spearman")
        ics.append({"trade_date": date, "IC": ic})
    if not ics:
        return pd.DataFrame(columns=["trade_date", "IC"])
    return pd.DataFrame(ics).set_index("trade_date")


def ic_summary(ic_series):
    ic = ic_series.dropna()
    if len(ic) == 0:
        return {"ic_mean": 0.0, "ic_std": 0.0, "ic_ir": 0.0, "ic_pos_ratio": 0.0, "n": 0}
    m = float(ic.mean())
    s = float(ic.std())
    return {
        "ic_mean": round(m, 6),
        "ic_std": round(s, 6),
        "ic_ir": round(m / s, 4) if s > 0 else 0.0,
        "ic_pos_ratio": round(float((ic > 0).mean()), 4),
        "n": len(ic),
    }


def build_portfolio(factor_df, fwd_ret_df, top_pct=TOP_PCT, cost_rate=COST_RATE):
    """Long-short portfolio: top 20% long, bottom 20% short."""
    factor = factor_df.copy()
    fwd = fwd_ret_df.copy()

    records = []
    for date in factor.index:
        if date not in fwd.index:
            continue
        sig = factor.loc[date].dropna()
        ret = fwd.loc[date].dropna()
        common = sig.index.intersection(ret.index)
        if len(common) < 10:
            continue

        sig = sig[common]
        ret = ret[common]

        # Z-score the signal
        sig_z = (sig - sig.mean()) / (sig.std() + 1e-10)
        n = max(1, int(len(sig_z) * top_pct))

        long_idx = sig_z.nlargest(n).index
        short_idx = sig_z.nsmallest(n).index

        long_ret = ret[long_idx].mean()
        short_ret = ret[short_idx].mean()
        spread = long_ret - short_ret

        # Turnover: estimate from signal rank change
        if records:
            prev_long = set(records[-1].get("long_stocks", []))
            prev_short = set(records[-1].get("short_stocks", []))
            curr_long = set(long_idx)
            curr_short = set(short_idx)
            turnover = 0.5 * (
                len(curr_long - prev_long) / max(len(curr_long), 1)
                + len(curr_short - prev_short) / max(len(curr_short), 1)
            )
        else:
            turnover = 1.0

        gross_ret = spread
        net_ret = gross_ret - turnover * cost_rate

        # Long-only top N
        long_only_ret = ret[long_idx].mean()

        records.append({
            "trade_date": date,
            "long_ret": long_ret,
            "short_ret": short_ret,
            "spread": spread,
            "gross_ret": gross_ret,
            "net_ret": net_ret,
            "turnover": turnover,
            "long_count": n,
            "short_count": n,
            "long_only_ret": long_only_ret,
            "long_stocks": list(long_idx),
            "short_stocks": list(short_idx),
        })

    return pd.DataFrame(records).set_index("trade_date")


def build_long_only_portfolio(factor_df, fwd_ret_df, n_stocks=50, cost_rate=COST_RATE):
    """Long-only portfolio: top N stocks, equally weighted."""
    factor = factor_df.copy()
    fwd = fwd_ret_df.copy()

    records = []
    prev_stocks = set()
    for date in factor.index:
        if date not in fwd.index:
            continue
        sig = factor.loc[date].dropna()
        ret = fwd.loc[date].dropna()
        common = sig.index.intersection(ret.index)
        if len(common) < n_stocks:
            continue

        sig = sig[common]
        ret = ret[common]
        sig_z = (sig - sig.mean()) / (sig.std() + 1e-10)
        top = sig_z.nlargest(n_stocks).index

        long_ret = ret[top].mean()
        curr = set(top)
        turnover = len(curr - prev_stocks) / max(len(curr), 1) if prev_stocks else 1.0
        net_ret = long_ret - turnover * cost_rate

        records.append({
            "trade_date": date,
            "long_only_ret": long_ret,
            "net_ret": net_ret,
            "turnover": turnover,
        })
        prev_stocks = curr

    return pd.DataFrame(records).set_index("trade_date")


def portfolio_metrics(returns_series, ann_factor=52):
    """Compute key portfolio metrics from returns."""
    r = returns_series.dropna()
    if len(r) == 0:
        return {"annual_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0,
                "calmar": 0.0, "win_rate": 0.0, "cum_return": 0.0}

    cum = (1 + r).cumprod()
    cum_ret = float(cum.iloc[-1] - 1)
    n = len(r)
    ann_ret = float((1 + cum_ret) ** (ann_factor / n) - 1) if n > 0 else 0.0
    ann_vol = float(r.std() * np.sqrt(ann_factor))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0
    dd = cum / cum.cummax() - 1
    max_dd = float(dd.min())
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0.0
    win_rate = float((r > 0).mean())

    return {
        "annual_return": round(ann_ret, 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "calmar": round(calmar, 4),
        "win_rate": round(win_rate, 4),
        "cum_return": round(cum_ret, 4),
    }
# --- Universe builders ---

def build_universe_current(weekly):
    train = weekly[(weekly['trade_date'] >= '2023-01-01') & (weekly['trade_date'] <= '2024-06-30')]
    vol_mean = train.groupby('ts_code')['volume'].mean().sort_values(ascending=False)
    return vol_mean.head(400).index.tolist()

def build_universe_amount_mid(weekly):
    train = weekly[(weekly['trade_date'] >= '2023-01-01') & (weekly['trade_date'] <= '2024-06-30')]
    amt = train.groupby('ts_code')['amount'].mean().sort_values(ascending=False)
    n = len(amt)
    lo = int(n * 0.20)
    hi = int(n * 0.80)
    mid = amt.iloc[lo:hi]
    if len(mid) > 400:
        mid = mid.head(400)
    return mid.index.tolist()

def build_universe_volclose_mid(weekly):
    train = weekly[(weekly['trade_date'] >= '2023-01-01') & (weekly['trade_date'] <= '2024-06-30')]
    train = train.copy()
    train['vol_close'] = train['volume'] * train['close']
    proxy = train.groupby('ts_code')['vol_close'].mean().sort_values(ascending=False)
    n = len(proxy)
    lo = int(n * 0.20)
    hi = int(n * 0.80)
    mid = proxy.iloc[lo:hi]
    if len(mid) > 400:
        mid = mid.head(400)
    return mid.index.tolist()

def build_universe_liquidity_filtered(weekly):
    train = weekly[(weekly['trade_date'] >= '2023-01-01') & (weekly['trade_date'] <= '2024-06-30')]
    n_days = train.groupby('ts_code').size()
    amt = train.groupby('ts_code')['amount'].mean()
    close = train.groupby('ts_code')['close'].mean()
    eligible = n_days[n_days >= 40].index
    eligible = eligible.intersection(amt[amt > amt.quantile(0.05)].index)
    eligible = eligible.intersection(close[close > 2.0].index)
    eligible = list(eligible)
    if len(eligible) > 400:
        top = amt[eligible].sort_values(ascending=False).head(400).index.tolist()
        return top
    return eligible


# --- Part 1: Strategy decomposition ---

def run_strategy_decomposition(weekly):
    import os
    import pandas as pd
    from diagnostics.followup_diagnosis import build_pivots, compute_fwd_ret, compute_simple_factor, build_portfolio, portfolio_metrics

    COST_RATE = 0.004

    universe = build_universe_current(weekly)
    pivots = build_pivots(weekly, universe, ['close', 'high', 'low', 'volume'])
    fwd = compute_fwd_ret(pivots['close'])
    ret = pivots['close'].pct_change(fill_method=None)
    factor = compute_simple_factor(pivots, '-volume')

    pf = build_portfolio(factor, fwd)

    hs300 = pd.read_parquet('data/hs300_weekly.parquet')
    hs300['trade_date'] = pd.to_datetime(hs300['trade_date'])
    hs300 = hs300.set_index('trade_date')['pct_chg'].sort_index()

    cyb = pd.read_parquet('data/cyb_weekly.parquet')
    cyb['trade_date'] = pd.to_datetime(cyb['trade_date'])
    cyb = cyb.set_index('trade_date')['pct_chg'].sort_index()

    univ_ew = fwd.mean(axis=1)

    rows = []
    for date in pf.index:
        row = {
            'trade_date': date,
            'strategy_net_ret': pf.loc[date, 'net_ret'],
            'strategy_gross_ret': pf.loc[date, 'gross_ret'],
            'long_leg_ret': pf.loc[date, 'long_ret'],
            'short_leg_ret': pf.loc[date, 'short_ret'],
            'long_short_spread': pf.loc[date, 'spread'],
            'turnover': pf.loc[date, 'turnover'],
            'long_count': pf.loc[date, 'long_count'],
            'short_count': pf.loc[date, 'short_count'],
        }
        if date in hs300.index:
            row['hs300_ret'] = hs300.loc[date]
        if date in cyb.index:
            row['cyb_ret'] = cyb.loc[date]
        if date in univ_ew.index:
            row['universe_equal_weight_ret'] = univ_ew.loc[date]
        rows.append(row)

    df = pd.DataFrame(rows).set_index('trade_date')
    df.to_parquet(os.path.join('report', 'diagnosis_weekly_decomposition.parquet'))

    print('=== PART 1: STRATEGY DECOMPOSITION ===')
    for col in ['strategy_gross_ret', 'strategy_net_ret', 'long_leg_ret', 'short_leg_ret', 'long_short_spread']:
        if col in df.columns:
            m = portfolio_metrics(df[col])
            print(f'{col}: ann={m["annual_return"]:.1%} sharpe={m["sharpe"]:.2f} maxdd={m["max_drawdown"]:.1%} cum={m["cum_return"]:.1%} win={m["win_rate"]:.1%}')

    print(f'turnover: mean={df["turnover"].mean():.3f} median={df["turnover"].median():.3f} p90={df["turnover"].quantile(0.9):.3f}')
    cost_per_week = df['turnover'].mean() * COST_RATE
    print(f'Avg cost/week: {cost_per_week:.4f} (annualized: {cost_per_week*52:.1%})')

    return df


# --- Part 2: Single factor tests ---

FACTORS = ['-ret_1w', '-ret_4w', '-vol_4w', '-volume', '-amplitude']

def run_single_factor_tests(weekly):
    import os
    import pandas as pd
    import numpy as np
    from diagnostics.followup_diagnosis import (build_pivots, compute_fwd_ret, compute_simple_factor,
                                                 compute_weekly_ic, ic_summary, build_portfolio,
                                                 build_long_only_portfolio, portfolio_metrics,
                                                 get_period_mask)

    universe = build_universe_current(weekly)
    pivots = build_pivots(weekly, universe, ['close', 'high', 'low', 'volume'])
    fwd_full = compute_fwd_ret(pivots['close'])

    periods = {'train': ('2023-01-01', '2024-06-30'),
               'val': ('2024-07-01', '2025-06-30'),
               'test': ('2025-07-01', None)}

    rows = []
    for factor_name in FACTORS:
        factor = compute_simple_factor(pivots, factor_name)

        for period_name, (start, end) in periods.items():
            mask = get_period_mask(factor.index.astype(str), start, end)
            f_period = factor[mask]
            fwd_mask = fwd_full.index.isin(f_period.index)
            fwd_period = fwd_full[fwd_mask]

            ic_df = compute_weekly_ic(f_period, fwd_period)
            ic_list = ic_df['IC'] if 'IC' in ic_df.columns else pd.Series(dtype=float)
            ic_s = ic_summary(ic_list)

            row = {
                'factor': factor_name, 'period': period_name,
                'ic_mean': ic_s['ic_mean'], 'ic_std': ic_s['ic_std'],
                'ic_ir': ic_s['ic_ir'], 'ic_pos_ratio': ic_s['ic_pos_ratio'], 'ic_n': ic_s['n'],
            }

            # Long-short
            pf_ls = build_portfolio(f_period, fwd_period)
            if len(pf_ls) > 0 and 'gross_ret' in pf_ls.columns:
                m_gross = portfolio_metrics(pf_ls['gross_ret'])
                m_net = portfolio_metrics(pf_ls['net_ret'])
                row.update({
                    'ls_gross_ann': m_gross['annual_return'], 'ls_gross_sharpe': m_gross['sharpe'],
                    'ls_gross_maxdd': m_gross['max_drawdown'],
                    'ls_net_ann': m_net['annual_return'], 'ls_net_sharpe': m_net['sharpe'],
                    'ls_net_maxdd': m_net['max_drawdown'],
                    'ls_turnover': float(pf_ls['turnover'].mean()) if 'turnover' in pf_ls.columns else 0,
                })
                if 'long_ret' in pf_ls.columns:
                    m_long = portfolio_metrics(pf_ls['long_ret'])
                    row['ls_long_leg_ann'] = m_long['annual_return']
                    row['ls_long_leg_sharpe'] = m_long['sharpe']
                if 'short_ret' in pf_ls.columns:
                    m_short = portfolio_metrics(pf_ls['short_ret'])
                    row['ls_short_leg_ann'] = m_short['annual_return']

            # Long-only top 50
            pf_lo50 = build_long_only_portfolio(f_period, fwd_period, n_stocks=50)
            if len(pf_lo50) > 0:
                m_lo50 = portfolio_metrics(pf_lo50['net_ret'])
                row.update({
                    'lo50_ann': m_lo50['annual_return'], 'lo50_sharpe': m_lo50['sharpe'],
                    'lo50_maxdd': m_lo50['max_drawdown'],
                    'lo50_turnover': float(pf_lo50['turnover'].mean()) if 'turnover' in pf_lo50.columns else 0,
                })

            # Long-only top 100
            pf_lo100 = build_long_only_portfolio(f_period, fwd_period, n_stocks=100)
            if len(pf_lo100) > 0:
                m_lo100 = portfolio_metrics(pf_lo100['net_ret'])
                row.update({
                    'lo100_ann': m_lo100['annual_return'], 'lo100_sharpe': m_lo100['sharpe'],
                    'lo100_maxdd': m_lo100['max_drawdown'],
                })

            # Universe equal weight benchmark (test period only)
            if period_name == 'test':
                ew = fwd_period.mean(axis=1)
                m_ew = portfolio_metrics(ew)
                row.update({
                    'univ_ew_ann': m_ew['annual_return'], 'univ_ew_sharpe': m_ew['sharpe'],
                    'univ_ew_maxdd': m_ew['max_drawdown'], 'univ_ew_cum': m_ew['cum_return'],
                })

            rows.append(row)

    result = pd.DataFrame(rows)
    result.to_parquet(os.path.join('report', 'single_factor_diagnosis.parquet'))

    print('=== PART 2: SINGLE FACTOR TESTS ===')
    display_cols = ['factor', 'period', 'ic_mean', 'ic_ir', 'ls_net_sharpe', 'lo50_sharpe', 'lo100_sharpe']
    avail = [c for c in display_cols if c in result.columns]
    print(result[avail].to_string())
    return result


# --- Part 3: Universe comparison ---

UNIVERSE_BUILDERS = {
    'U1_current_top400_volume': build_universe_current,
    'U2_amount_middle_60pct': build_universe_amount_mid,
    'U3_volclose_middle_60pct': build_universe_volclose_mid,
    'U4_liquidity_filtered': build_universe_liquidity_filtered,
}

def run_universe_comparison(weekly):
    import os
    import pandas as pd
    from diagnostics.followup_diagnosis import (build_pivots, compute_fwd_ret, compute_simple_factor,
                                                 compute_weekly_ic, ic_summary, build_portfolio,
                                                 build_long_only_portfolio, portfolio_metrics,
                                                 get_period_mask)

    rows = []

    for uname, builder in UNIVERSE_BUILDERS.items():
        universe = builder(weekly)
        print(f'{uname}: {len(universe)} stocks')

        pivots = build_pivots(weekly, universe, ['close', 'high', 'low', 'volume'])
        fwd_full = compute_fwd_ret(pivots['close'])

        for factor_name in FACTORS:
            factor = compute_simple_factor(pivots, factor_name)

            for period_name, start, end in [('val', '2024-07-01', '2025-06-30'),
                                               ('test', '2025-07-01', None)]:
                mask = get_period_mask(factor.index.astype(str), start, end)
                f_period = factor[mask]
                fwd_mask = fwd_full.index.isin(f_period.index)
                fwd_period = fwd_full[fwd_mask]

                ic_df = compute_weekly_ic(f_period, fwd_period)
                ic_list = ic_df['IC'] if 'IC' in ic_df.columns else pd.Series(dtype=float)
                ic_s = ic_summary(ic_list)

                row = {
                    'universe': uname, 'factor': factor_name, 'period': period_name,
                    'ic_mean': ic_s['ic_mean'], 'ic_ir': ic_s['ic_ir'],
                    'universe_size': len(universe),
                }

                pf_ls = build_portfolio(f_period, fwd_period)
                if len(pf_ls) > 0 and 'net_ret' in pf_ls.columns:
                    m = portfolio_metrics(pf_ls['net_ret'])
                    row.update({'ls_net_ann': m['annual_return'], 'ls_net_sharpe': m['sharpe'],
                                'ls_maxdd': m['max_drawdown'],
                                'ls_turnover': float(pf_ls['turnover'].mean()) if 'turnover' in pf_ls.columns else 0})

                pf_lo50 = build_long_only_portfolio(f_period, fwd_period, n_stocks=50)
                if len(pf_lo50) > 0:
                    m = portfolio_metrics(pf_lo50['net_ret'])
                    row.update({'lo50_ann': m['annual_return'], 'lo50_sharpe': m['sharpe'],
                                'lo50_maxdd': m['max_drawdown']})

                ew = fwd_period.mean(axis=1)
                mew = portfolio_metrics(ew)
                row.update({'univ_ew_ann': mew['annual_return'], 'univ_ew_sharpe': mew['sharpe']})

                if period_name == 'test' and 'lo50_ann' in row:
                    row['excess_lo50_vs_ew'] = round(row['lo50_ann'] - mew['annual_return'], 4)

                rows.append(row)

    result = pd.DataFrame(rows)
    result.to_parquet(os.path.join('report', 'universe_factor_comparison.parquet'))

    print('=== PART 3: UNIVERSE COMPARISON (test period, lo50) ===')
    test_rows = result[result['period'] == 'test'] if 'period' in result.columns else pd.DataFrame()
    if len(test_rows) > 0:
        for uname in UNIVERSE_BUILDERS:
            sub = test_rows[test_rows['universe'] == uname]
            if len(sub) > 0 and 'lo50_sharpe' in sub.columns:
                best_idx = sub['lo50_sharpe'].idxmax()
                best = sub.loc[best_idx]
                print(f'{uname}: best_lo50_sharpe={best["lo50_sharpe"]:.3f} excess_vs_ew={best.get("excess_lo50_vs_ew", 0):.4f}')

    return result


# --- Part 4: IC_IR threshold grid ---

def run_icir_threshold_grid(weekly):
    import os
    import pandas as pd
    import numpy as np
    from diagnostics.followup_diagnosis import (build_pivots, compute_fwd_ret, compute_simple_factor,
                                                 compute_weekly_ic, ic_summary, build_portfolio,
                                                 portfolio_metrics, get_period_mask)

    universe = build_universe_current(weekly)
    pivots = build_pivots(weekly, universe, ['close', 'high', 'low', 'volume'])
    fwd_full = compute_fwd_ret(pivots['close'])

    val_mask = get_period_mask(fwd_full.index.astype(str), '2024-07-01', '2025-06-30')
    test_mask = get_period_mask(fwd_full.index.astype(str), '2025-07-01', None)

    factor_val_icir = {}
    for fname in FACTORS:
        factor = compute_simple_factor(pivots, fname)
        val_f = factor[val_mask]
        val_fwd = fwd_full[fwd_full.index.isin(val_f.index)]
        ic_df = compute_weekly_ic(val_f, val_fwd)
        if 'IC' in ic_df.columns and len(ic_df) > 0:
            ic_s = ic_summary(ic_df['IC'])
            factor_val_icir[fname] = abs(ic_s['ic_ir'])

    print(f'Factor val IC_IR: {factor_val_icir}')

    thresholds = [0.05, 0.10, 0.20, 0.30, 0.50]
    max_counts = [3, 5, 10, 20]

    rows = []
    for thresh in thresholds:
        selected = sorted([f for f, icir in factor_val_icir.items() if icir >= thresh],
                          key=lambda f: factor_val_icir[f], reverse=True)

        for max_n in max_counts:
            use = selected[:max_n]
            if len(use) == 0:
                rows.append({'threshold': thresh, 'max_count': max_n, 'selected_count': 0,
                             'gross_ann': 0, 'net_ann': 0, 'net_sharpe': 0, 'net_maxdd': 0})
                continue

            combined_gross = None
            combined_net = None

            for fname in use:
                factor = compute_simple_factor(pivots, fname)
                test_f = factor[test_mask]
                test_fwd = fwd_full[fwd_full.index.isin(test_f.index)]
                pf = build_portfolio(test_f, test_fwd)
                if len(pf) > 0 and 'gross_ret' in pf.columns:
                    if combined_gross is None:
                        combined_gross = pf['gross_ret']
                        combined_net = pf['net_ret']
                    else:
                        ci = combined_gross.index.intersection(pf['gross_ret'].index)
                        if len(ci) > 0:
                            combined_gross = combined_gross[ci] + pf['gross_ret'][ci]
                            combined_net = combined_net[ci] + pf['net_ret'][ci]

            if combined_gross is not None and len(combined_gross) > 0:
                combined_gross = combined_gross / len(use)
                combined_net = combined_net / len(use)
                m_gross = portfolio_metrics(combined_gross)
                m_net = portfolio_metrics(combined_net)
                rows.append({
                    'threshold': thresh, 'max_count': max_n, 'selected_count': len(use),
                    'gross_ann': m_gross['annual_return'], 'gross_sharpe': m_gross['sharpe'],
                    'net_ann': m_net['annual_return'], 'net_sharpe': m_net['sharpe'],
                    'net_maxdd': m_net['max_drawdown'],
                })
            else:
                rows.append({'threshold': thresh, 'max_count': max_n, 'selected_count': len(use),
                             'gross_ann': 0, 'net_ann': 0, 'net_sharpe': 0, 'net_maxdd': 0})

    result = pd.DataFrame(rows)
    result.to_parquet(os.path.join('report', 'icir_threshold_grid.parquet'))
    print('=== PART 4: IC_IR THRESHOLD GRID ===')
    print(result.to_string())
    return result


# --- Main ---

def main():
    import pandas as pd
    from diagnostics.followup_diagnosis import load_data

    print('='*60)
    print('claudets follow-up diagnosis')
    print('='*60)

    weekly, hs300_ret, cyb_ret = load_data()
    print(f'Data: {len(weekly)} rows ({weekly["trade_date"].min().date()} to {weekly["trade_date"].max().date()})')

    decomp = run_strategy_decomposition(weekly)
    single_factor = run_single_factor_tests(weekly)
    universe_comp = run_universe_comparison(weekly)
    icir_grid = run_icir_threshold_grid(weekly)

    print()
    print('All diagnostic data files written to report/')
    return decomp, single_factor, universe_comp, icir_grid


if __name__ == '__main__':
    main()
