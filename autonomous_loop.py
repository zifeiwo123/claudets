"""Autonomous iteration system - all critical bugs fixed.

Fixes applied:
- Task 3: unique factor IDs + correct structure hash
- Task 4: negative-IC factors flipped based on val_IC direction
- Task 5: transaction cost subtractive (turnover * cost_rate), not multiplicative
- Task 6: removed post-hoc drawdown clip
- Task 7: stock universe fixed at train-period top stocks
- Task 9: weekly dates use last real trade date (fixed in preprocessor separately)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os, json, re
from datetime import datetime

from config.settings import WEEKLY_PARQUET
from data.daily_feature_builder import DAILY_FEATURE_COLUMNS, ensure_weekly_daily_features
from factors.factor_compute import FactorCompute
from factors.factor_pool import FactorPool
from factors.factor_generator import FactorGenerator
from factors.expression_tree import ExprNode
from evolution.constraints import ConstraintChecker
from evolution.engine import EvolutionEngine
from evaluation.ic_analysis import ICAnalyzer
from portfolio.metrics import PerformanceMetrics
from portfolio.weight_schemes import WeightSchemes

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

SLIPPAGE_ONE_WAY = 0.002   # 0.2% one-side
TURNOVER_COST_RATE = 0.004  # cost per 1.0 turnover, applied as turnover * rate
MAX_STOCKS = 400
REPORT_DIR = 'report'
ELITE_POOL_PATH = os.path.join(REPORT_DIR, "elite_pool.json")
ELITE_POOL_SIZE = 10
os.makedirs(REPORT_DIR, exist_ok=True)


def save_result_tables(results):
    if not results:
        return
    summary_path = os.path.join(REPORT_DIR, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    pd.DataFrame(results).to_csv(os.path.join(REPORT_DIR, 'iteration_summary.csv'), index=False)


def infer_start_iteration(existing):
    if existing:
        return max(int(row.get('iteration', 0)) for row in existing) + 1
    max_report_iter = 0
    for name in os.listdir(REPORT_DIR):
        match = re.fullmatch(r"report_v(\d+)\.md", name)
        if match:
            max_report_iter = max(max_report_iter, int(match.group(1)))
    return max_report_iter + 1 if max_report_iter else 1


def load_data():
    weekly = ensure_weekly_daily_features()
    weekly['trade_date'] = pd.to_datetime(weekly['trade_date'])
    train = weekly[(weekly['trade_date'] >= '2023-01-01') & (weekly['trade_date'] <= '2024-06-30')].copy()
    val = weekly[(weekly['trade_date'] >= '2024-07-01') & (weekly['trade_date'] <= '2025-06-30')].copy()
    test = weekly[(weekly['trade_date'] >= '2025-07-01')].copy()

    hs300 = pd.read_parquet('data/hs300_weekly.parquet')
    hs300['trade_date'] = pd.to_datetime(hs300['trade_date'])
    hs300 = hs300.sort_values('trade_date')
    hs300_ret = hs300.set_index('trade_date')['pct_chg']

    cyb = pd.read_parquet('data/cyb_weekly.parquet')
    cyb['trade_date'] = pd.to_datetime(cyb['trade_date'])
    cyb = cyb.sort_values('trade_date')
    cyb_ret = cyb.set_index('trade_date')['pct_chg']

    return train, val, test, hs300_ret, cyb_ret


def get_universe_stocks(train_data, n=MAX_STOCKS):
    """Task 7: Fixed universe from training period only (no future info)"""
    vol_col = "volume" if "volume" in train_data.columns else "vol"
    vol_mean = train_data.groupby("ts_code")[vol_col].mean().sort_values(ascending=False)
    return vol_mean.head(n).index.tolist()


def daily_feature_coverage(df):
    cols = [col for col in DAILY_FEATURE_COLUMNS if col in df.columns]
    if not cols:
        return 0.0
    return float(df[cols].notna().mean().mean())



def load_elite_pool():
    """Load persistent elite factors from previous iterations"""
    if not os.path.exists(ELITE_POOL_PATH):
        return []
    checker = ConstraintChecker()
    try:
        with open(ELITE_POOL_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        elites = []
        for entry in data:
            try:
                node = ExprNode.from_dict(entry["tree"])
                if not checker.validate(node):
                    continue
                elites.append({
                    "id": entry["id"], "node": node,
                    "expr": str(node), "val_ic": entry["val_ic"],
                    "val_icir": entry["val_icir"], "direction": entry["direction"],
                    "score": entry["score"], "iteration": entry.get("iteration", 0),
                })
            except Exception:
                pass
        return elites
    except Exception as e:
        print(f"  [WARN] Failed to load elite pool: {e}")
        return []



def save_elite_pool_from_pool(pool, eval_df, iteration):
    """Save top factors with their tree structures"""
    if len(eval_df) == 0:
        return
    # Merge eval_df with pool nodes
    elite_entries = []
    top = eval_df.nlargest(ELITE_POOL_SIZE, "score")
    for _, r in top.iterrows():
        fid = r["id"]
        node = pool.get(fid)
        if node is None:
            continue
        elite_entries.append({
            "id": fid,
            "tree": node.to_dict(),
            "val_ic": float(r["ic_va"]),
            "val_icir": float(r["icir_va"]),
            "direction": "LONG" if r.get("direction", 0) >= 0 else "SHORT",
            "score": float(r["score"]),
            "iteration": iteration,
            "expr": str(node),
        })
    if elite_entries:
        with open(ELITE_POOL_PATH, 'w', encoding='utf-8') as f:
            json.dump(elite_entries, f, indent=2, ensure_ascii=False)
        print(f"  [ELITE] Saved {len(elite_entries)} factors to elite pool")
def generate_and_evaluate(train, val, universe, elite_seeds=None, n_initial=20):
    """Generate factors + evaluate on train/val"""
    checker = ConstraintChecker()
    generator = FactorGenerator(checker)

    all_factors = []
    for batch in range(4):
        all_factors.extend(generator.generate_pool(8))
        np.random.seed(np.random.randint(0, 2**31 - 1))

    pool = FactorPool()
    for fid, node, explanation in all_factors:
        pool.add(fid, node, generation=0)

    # Inject elite seeds from previous iterations
    n_elite = 0
    if elite_seeds:
        for es in elite_seeds:
            try:
                node = es["node"]
                if not checker.validate(node):
                    continue
                fid = f"elite_{FactorGenerator._next_id:04d}"
                FactorGenerator._next_id += 1
                pool.add(fid, node, generation=-1)  # gen=-1 marks elite
                n_elite += 1
            except Exception:
                pass
    if n_elite > 0:
        print(f"  [ELITE] Seeded {n_elite} elite factors from previous rounds")

    # Filter data to universe
    train_u = train[train['ts_code'].isin(universe)]
    val_u = val[val['ts_code'].isin(universe)]

    train_comp = FactorCompute(train_u, max_stocks=MAX_STOCKS, universe=universe)
    val_comp = FactorCompute(val_u, max_stocks=MAX_STOCKS, universe=universe)

    fwd_train = train_comp._data['close'].shift(-1) / train_comp._data['close'] - 1
    fwd_train = fwd_train.stack(); fwd_train.index.names = ['trade_date','ts_code']
    fwd_val = val_comp._data['close'].shift(-1) / val_comp._data['close'] - 1
    fwd_val = fwd_val.stack(); fwd_val.index.names = ['trade_date','ts_code']

    eval_results = []
    for fid in pool.list_ids():
        node = pool.get(fid)
        if node is None: continue
        try:
            fv_tr = train_comp.compute(node, fid)
            ic_tr = ICAnalyzer(fv_tr, fwd_train).compute_ic_summary()
            fv_va = val_comp.compute(node, fid)
            ic_va = ICAnalyzer(fv_va, fwd_val).compute_ic_summary()
            # Task 4: Record IC direction for signal flipping
            direction = 1 if ic_va.get('ic_mean', 0) >= 0 else -1
            ic_va['direction'] = direction
            ic_va['adjusted_ic'] = ic_va['ic_mean'] * direction
            ic_va['train_ic_mean'] = ic_tr['ic_mean']
            ic_va['train_ic_ir'] = ic_tr['ic_ir']
            pool.update_ic_results({fid: ic_va})

            cs = abs(ic_tr['ic_mean'] - ic_va['ic_mean'])
            score = (abs(ic_va['ic_ir']) * 0.5 +
                     (1.0 - min(cs * 10, 1.0)) * 0.3 +
                     (1.0 if np.sign(ic_tr['ic_mean']) == np.sign(ic_va['ic_mean']) else 0.0) * 0.2)

            eval_results.append({
                'id': fid, 'depth': node.get_depth(), 'expr': str(node),
                'ic_tr': ic_tr['ic_mean'], 'icir_tr': ic_tr['ic_ir'],
                'ic_va': ic_va['ic_mean'], 'icir_va': ic_va['ic_ir'],
                'direction': direction, 'adj_ic': ic_va['adjusted_ic'],
                'cs': cs, 'score': score,
            })
        except Exception:
            pass

    return pool, pd.DataFrame(eval_results), train_comp, val_comp


def run_evolution(train, val, universe, pool, good_df):
    """Run evolution on filtered universe"""
    train_u = train[train['ts_code'].isin(universe)]
    val_u = val[val['ts_code'].isin(universe)]

    engine = EvolutionEngine(train_u, val_u, universe=universe, max_stocks=MAX_STOCKS)
    checker = ConstraintChecker()
    for _, r in good_df.iterrows():
        node = pool.get(r['id'])
        if node and checker.validate(node):
            engine.pool.add(r['id'], node, generation=0)

    result = engine.run()
    return engine, result


def backtest_portfolio(test, universe, engine, factor_signals, fwd_test, ic_results):
    """Portfolio backtest with all fixes applied"""
    usable_ids = [fid for fid in ic_results if abs(ic_results[fid].get('ic_ir', 0)) > 0.05]
    if len(usable_ids) < 5:
        usable_ids = [fid for fid in ic_results if abs(ic_results[fid].get('ic_ir', 0)) > 0.02]
    if len(usable_ids) < 3:
        usable_ids = list(ic_results.keys())

    # Task 4: Flip signals for negative-IC factors
    flipped_signals = {}
    for fid in usable_ids:
        if fid not in factor_signals:
            continue
        ic = ic_results.get(fid, {})
        direction = int(ic.get('direction', 1 if ic.get('ic_mean', 0) >= 0 else -1))
        flipped_signals[fid] = factor_signals[fid] * direction

    usable_ic = {fid: ic_results[fid] for fid in usable_ids if fid in ic_results}

    schemes = WeightSchemes(flipped_signals, fwd_test)
    rets_eq = schemes.equal_weight()
    rets_icir = schemes.icir_weight(usable_ic) if len(usable_ic) > 2 else rets_eq

    rets_raw = rets_icir if len(rets_icir) > 0 else rets_eq
    if len(rets_raw) == 0:
        return None, None, None

    # Task 5: Subtract turnover-based cost (NOT multiplicative).
    turnover = getattr(schemes, "last_turnover", None)
    if turnover is None or len(turnover) == 0:
        turnover = pd.Series(1.0, index=rets_raw.index)
    turnover = turnover.reindex(rets_raw.index).fillna(1.0)
    rets_net = rets_raw - turnover * TURNOVER_COST_RATE
    rets_net = rets_net.dropna()

    # Task 6: Forward-looking vol timing only (NO post-hoc clip)
    rolling_vol = rets_net.shift(1).rolling(12).std() * np.sqrt(52)
    hist_vol = rolling_vol.shift(1).rolling(52).mean()
    vol_spike = (rolling_vol > 1.5 * hist_vol).fillna(False)
    scale = pd.Series(1.0, index=rets_net.index)
    scale[vol_spike] = 0.5
    rets_final = rets_net * scale

    if len(rets_final) > 0:
        metrics = PerformanceMetrics(rets_final).compute_all()
        return rets_final, metrics, flipped_signals

    return None, None, None


def build_pool_eval_df(pool):
    """Build a report table from the final evolved pool and validation metrics."""
    rows = []
    for fid in pool.list_ids():
        node = pool.get(fid)
        ic = pool.get_ic_result(fid) or {}
        if node is None or not ic:
            continue
        val_ic = float(ic.get("ic_mean", 0))
        direction = int(ic.get("direction", 1 if val_ic >= 0 else -1))
        train_ic = float(ic.get("train_ic_mean", 0))
        train_icir = float(ic.get("train_ic_ir", 0))
        val_icir = float(ic.get("ic_ir", 0))
        consistency = 1.0 if np.sign(train_ic) == np.sign(val_ic) else 0.0
        score = abs(val_icir) * 0.5 + abs(val_ic) * 2.0 + consistency * 0.2
        rows.append({
            "id": fid,
            "depth": node.get_depth(),
            "expr": str(node),
            "ic_tr": train_ic,
            "icir_tr": train_icir,
            "ic_va": val_ic,
            "icir_va": val_icir,
            "direction": direction,
            "adj_ic": val_ic * direction,
            "score": score,
        })
    return pd.DataFrame(rows)


def align_benchmark(strat_dates, bench_ret):
    """Align benchmark returns to strategy dates"""
    strat_dates = pd.to_datetime(strat_dates)
    bench_idx = bench_ret.index
    shifted = strat_dates - pd.Timedelta(days=1)
    result = {}
    for i, dt in enumerate(shifted):
        closest = bench_idx[bench_idx >= dt - pd.Timedelta(days=2)]
        if len(closest) > 0:
            match = closest[0]
            if abs((match - dt).days) <= 3:
                result[strat_dates[i]] = bench_ret.loc[match]
    return pd.Series(result)


def generate_chart(rets_final, hs300_ret, cyb_ret, metrics, iteration, report_path):
    """Generate comparison chart"""
    cum_strat = (1 + rets_final).cumprod()
    hs300_aligned = align_benchmark(rets_final.index, hs300_ret)
    cyb_aligned = align_benchmark(rets_final.index, cyb_ret)
    cum_hs300 = (1 + hs300_aligned).cumprod().ffill()
    cum_cyb = (1 + cyb_aligned).cumprod().ffill()

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(cum_strat.index, cum_strat.values, '#1a73e8', linewidth=2.5, label='Alpha Strategy')
    ax.plot(cum_hs300.index, cum_hs300.values, '#ea4335', linewidth=1.5, linestyle='--', label='CSI 300')
    ax.plot(cum_cyb.index, cum_cyb.values, '#34a853', linewidth=1.5, linestyle='--', label='ChiNext')

    ax.fill_between(cum_strat.index, 1.0, cum_strat.values,
                     where=cum_strat.values >= 1.0, alpha=0.1, color='green')
    ax.fill_between(cum_strat.index, cum_strat.values, 1.0,
                     where=cum_strat.values < 1.0, alpha=0.1, color='red')

    strat_final = (cum_strat.iloc[-1] - 1) * 100
    hs300_final = (cum_hs300.dropna().iloc[-1] - 1) * 100 if len(cum_hs300.dropna()) > 0 else 0
    cyb_final = (cum_cyb.dropna().iloc[-1] - 1) * 100 if len(cum_cyb.dropna()) > 0 else 0

    info_text = (
        f'Strategy: {strat_final:+.1f}% | ChiNext: {cyb_final:+.1f}% | CSI 300: {hs300_final:+.1f}%\n'
        f'Ann.Ret={metrics["annual_return"]:.1%} | Sharpe={metrics["sharpe_ratio"]:.2f} | MaxDD={metrics["max_drawdown"]:.1%}'
    )
    ax.text(0.02, 0.97, info_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.axhline(y=1.0, color='black', linewidth=0.5)
    ax.set_ylabel('Cumulative Return', fontsize=12)
    ax.set_title(f'Alpha Factor Strategy vs Benchmarks [Iteration {iteration}]', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(report_path, dpi=150, bbox_inches='tight')
    plt.close()
    return strat_final, hs300_final, cyb_final


def generate_report(iteration, metrics, rets_final, hs300_ret, cyb_ret,
                    eval_df, engine):
    """Generate versioned report"""
    chart_path = os.path.join(REPORT_DIR, f'report_v{iteration}_chart.png')
    strat_final, hs300_final, cyb_final = generate_chart(
        rets_final, hs300_ret, cyb_ret, metrics, iteration, chart_path)

    lines = [f'# Alpha Factor Evolution Report - Iteration {iteration}',
             f'', f'**Time**: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
             f'',
             f'## Data Specification',
             f'- Source: Tushare daily K-line; daily rolling features sampled on each week last trading day',
             f'- Universe: Top {MAX_STOCKS} stocks by training-period volume (fixed, no future info)',
             f'- Frequency: Weekly rebalancing',
             f'- Signal granularity: daily-derived features, weekly decision snapshot',
             f'- Short selling: Long-short (top 20% long / bottom 20% short)',
             f'- Cost: turnover * {TURNOVER_COST_RATE:.1%} per rebalance',
             f'- Drawdown control: Forward-looking vol timing only (no post-hoc clip)',
             f'',
             f'## Performance Summary',
             f'',
             f'| Metric | Strategy | CSI 300 | ChiNext |',
             f'|--------|----------|---------|---------|',
             f'| Cumulative Return | {strat_final:+.1f}% | {hs300_final:+.1f}% | {cyb_final:+.1f}% |']

    if metrics:
        lines.append(f'| Annual Return | {metrics["annual_return"]:.1%} | - | - |')
        lines.append(f'| Sharpe Ratio | {metrics["sharpe_ratio"]:.2f} | - | - |')
        lines.append(f'| Max Drawdown | {metrics["max_drawdown"]:.1%} | - | - |')
        lines.append(f'| Calmar Ratio | {metrics["calmar_ratio"]:.2f} | - | - |')
        lines.append(f'| Weekly Win Rate | {metrics["weekly_win_rate"]:.1%} | - | - |')

    lines.extend(['', f'![Returns](report_v{iteration}_chart.png)', ''])


    # IC distribution
    if len(eval_df) > 0:
        n_pos = int((eval_df["ic_va"] > 0).sum())
        n_neg = int((eval_df["ic_va"] < 0).sum())
        pos_ic = eval_df[eval_df["ic_va"] > 0]["ic_va"]
        neg_ic = eval_df[eval_df["ic_va"] < 0]["ic_va"]
        lines.extend(["## Factor IC Distribution", "",
                       "| Direction | Count | Mean |IC| | Best |IC| | Best ICIR |",
                       "|-----------|-------|-----------|-----------|-----------|"])
        if n_pos > 0:
            lines.append(f"| LONG (+)  | {n_pos} | {pos_ic.abs().mean():.4f} | {pos_ic.max():.4f} | {eval_df[eval_df['ic_va']>0]['icir_va'].max():.3f} |")
        else:
            lines.append("| LONG (+)  | 0 | - | - | - |")
        if n_neg > 0:
            lines.append(f"| SHORT (-) | {n_neg} | {neg_ic.abs().mean():.4f} | {neg_ic.min():.4f} | {eval_df[eval_df['ic_va']<0]['icir_va'].min():.3f} |")
        else:
            lines.append("| SHORT (-) | 0 | - | - | - |")
        lines.append("")
    if len(eval_df) > 0:
        top = eval_df.nlargest(8, 'score')
        lines.extend(['## Top Factors (with direction applied)',
                       '',
                       '| ID | Expression | Train IC | Val IC | Val IC_IR | Direction | Score |',
                       '|----|-----------|----------|--------|-----------|-----------|-------|'])
        for _, r in top.iterrows():
            d = 'LONG' if r.get('direction', 0) >= 0 else 'SHORT'
            lines.append(f'| {r["id"]} | `{r["expr"]}` | {r["ic_tr"]:.4f} | {r["ic_va"]:.4f} | {r["icir_va"]:.3f} | {d} | {r["score"]:.3f} |')

    lines.extend(['',
                   '## Implementation Status',
                   '',
                   '| Feature | Status |',
                   '|---------|--------|',
                   '| Auto factor generation | Implemented |',
                   '| Train/val/test split | Implemented |',
                   '| IC evaluation (Spearman) | Implemented |',
                   '| Genetic evolution (mutation + crossover) | Implemented |',
                   '| Daily-derived signal features | Implemented |',
                   '| Signal direction flipping (neg IC) | Implemented |',
                   '| Fixed universe (no future info) | Implemented |',
                   '| Turnover-based transaction cost | Implemented |',
                   '| Forward vol timing (no post-hoc clip) | Implemented |',
                   '| Market-cap-tiered slippage | Partial (fixed rate used) |',
                   '| Industry/size neutralization | Not yet |',
                   '| Long-only portfolio | Not yet |',
                   '| Final holdout validation | Not yet |',
                   '| Forward-adjusted prices (qfq) | Not yet |',
                   ''])

    report_md = os.path.join(REPORT_DIR, f'report_v{iteration}.md')
    with open(report_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return report_md


def run_one_iteration(iteration, train, val, test, hs300_ret, cyb_ret, universe, elite_seeds=None):
    """Run one complete iteration"""
    t0 = datetime.now()

    pool, eval_df, train_comp, val_comp = generate_and_evaluate(train, val, universe, elite_seeds=elite_seeds, n_initial=20)

    good = eval_df[(eval_df['icir_va'].abs() > 0.05) | (eval_df['ic_va'].abs() > 0.015)]
    if len(good) < 3:
        good = eval_df.nlargest(5, 'score')
    good = good.sort_values('score', ascending=False)

    engine, evo_result = run_evolution(train, val, universe, pool, good)

    # Show IC direction distribution for this iteration
    if len(eval_df) > 0:
        n_pos = int((eval_df["ic_va"] > 0).sum())
        n_neg = int((eval_df["ic_va"] < 0).sum())
        pos_best = eval_df[eval_df["ic_va"] > 0]["ic_va"].max() if n_pos > 0 else 0
        neg_best = eval_df[eval_df["ic_va"] < 0]["ic_va"].min() if n_neg > 0 else 0
        print(f'  [IC] {len(eval_df)} factors: {n_pos} LONG (best IC={pos_best:+.4f}), {n_neg} SHORT (best IC={neg_best:+.4f})')

    # Test set backtest on fixed universe
    test_u = test[test['ts_code'].isin(universe)]
    test_comp = FactorCompute(test_u, max_stocks=MAX_STOCKS, universe=universe)
    factor_signals = {}
    for fid in engine.pool.list_ids():
        node = engine.pool.get(fid)
        if node is None: continue
        try: factor_signals[fid] = test_comp.compute(node, fid)
        except: pass

    fwd_test = test_comp._data['close'].shift(-1) / test_comp._data['close'] - 1
    fwd_test = fwd_test.stack(); fwd_test.index.names = ['trade_date','ts_code']

    ic_results = {}
    for fid in engine.pool.list_ids():
        ic = engine.pool.get_ic_result(fid)
        if ic: ic_results[fid] = ic

    rets_final, metrics, _ = backtest_portfolio(test, universe, engine, factor_signals, fwd_test, ic_results)

    if rets_final is None or len(rets_final) < 5:
        return None

    final_eval_df = build_pool_eval_df(engine.pool)
    report_path = generate_report(iteration, metrics, rets_final, hs300_ret, cyb_ret, final_eval_df, engine)
    save_elite_pool_from_pool(engine.pool, final_eval_df, iteration)

    elapsed = (datetime.now() - t0).total_seconds()
    cum_strat = (1 + rets_final).cumprod()
    strat_final = (cum_strat.iloc[-1] - 1) * 100
    cyb_aligned = align_benchmark(rets_final.index, cyb_ret)
    cyb_final = ((1 + cyb_aligned).cumprod().ffill().dropna().iloc[-1] - 1) * 100
    hs300_aligned = align_benchmark(rets_final.index, hs300_ret)
    hs300_final = ((1 + hs300_aligned).cumprod().ffill().dropna().iloc[-1] - 1) * 100

    ann = metrics['annual_return'] if metrics else 0
    sharpe = metrics['sharpe_ratio'] if metrics else 0
    maxdd = metrics['max_drawdown'] if metrics else 0

    print(f'  [ITER {iteration:3d}] Ann={ann:.1%}  Sharpe={sharpe:.2f}  MaxDD={maxdd:.1%}  '
          f'Strat={strat_final:+.1f}%  ChiNext={cyb_final:+.1f}%  HS300={hs300_final:+.1f}%  ({elapsed:.0f}s)')

    return {
        'iteration': iteration, 'annual_return': ann, 'sharpe': sharpe,
        'max_dd': maxdd, 'strat_cum': strat_final, 'cyb_cum': cyb_final,
        'hs300_cum': hs300_final, 'time': elapsed, 'report': report_path,
    }


def main():
    EPOCHS = int(os.getenv("CLAUDETS_EPOCHS", "50"))
    print(f'{"="*60}')
    train, val, test, hs300_ret, cyb_ret = load_data()
    universe = get_universe_stocks(train, n=MAX_STOCKS)
    print(f'Data ready. Fixed universe: {len(universe)} stocks (from training period)')
    print(f'Train={len(train)}, Val={len(val)}, Test={len(test)}')

    # Load existing results
    summary_path = os.path.join(REPORT_DIR, 'summary.json')
    existing = []
    if os.path.exists(summary_path):
        with open(summary_path, encoding='utf-8') as f:
            existing = json.load(f)
    START_ITER = int(os.getenv("CLAUDETS_START_ITER", str(infer_start_iteration(existing))))
    print(f'Autonomous Alpha Evolution - Iterations {START_ITER}-{START_ITER+EPOCHS-1} (daily-feature constrained)')
    print(f'{"="*60}')
    print(f'Existing results: {len(existing)} iterations')

    best_result = None
    all_results = list(existing)

    elite_seeds = load_elite_pool()
    print(f"Elite pool: {len(elite_seeds)} factors from previous rounds")
    for i in range(START_ITER, START_ITER + EPOCHS):
        result = run_one_iteration(i, train, val, test, hs300_ret, cyb_ret, universe, elite_seeds=elite_seeds)
        if result is None: continue
        all_results.append(result)
        save_result_tables(all_results)
        if best_result is None or result['sharpe'] > best_result['sharpe']:
            best_result = result
            print(f'  >>> NEW BEST: Sharpe={result["sharpe"]:.2f}  Ann={result["annual_return"]:.1%}')

    # Distribution summary (Task: show all iterations, not just best)
    print(f'\n{"="*60}')
    print(f' ITERATIONS {START_ITER}-{START_ITER+EPOCHS-1} COMPLETE')
    print(f'{"="*60}')
    print(f'Successful this batch: {len(all_results) - len(existing)}/{EPOCHS}')
    print(f'Total results: {len(all_results)}')

    if all_results:
        df_all = pd.DataFrame(all_results)
        print(f'\nDistribution:')
        print(f'  Sharpe: mean={df_all["sharpe"].mean():.2f}  median={df_all["sharpe"].median():.2f}  '
              f'min={df_all["sharpe"].min():.2f}  max={df_all["sharpe"].max():.2f}')
        print(f'  Ann.Ret: mean={df_all["annual_return"].mean():.1%}  median={df_all["annual_return"].median():.1%}')
        print(f'  MaxDD: mean={df_all["max_dd"].mean():.1%}  median={df_all["max_dd"].median():.1%}')
        print(f'  Beat HS300: {(df_all["strat_cum"]>df_all["hs300_cum"]).mean():.1%}')
        print(f'  Beat ChiNext: {(df_all["strat_cum"]>df_all["cyb_cum"]).mean():.1%}')
        print(f'  MaxDD>15%: {(df_all["max_dd"]<-0.15).mean():.1%}')

        if best_result:
            print(f'\nBest (by Sharpe): Iter {best_result["iteration"]}')
            print(f'  Ann.Ret={best_result["annual_return"]:.1%}  Sharpe={best_result["sharpe"]:.2f}  '
                  f'MaxDD={best_result["max_dd"]:.1%}')
            print(f'  Strat={best_result["strat_cum"]:+.1f}%  '
                  f'ChiNext={best_result["cyb_cum"]:+.1f}%  HS300={best_result["hs300_cum"]:+.1f}%')

        save_result_tables(all_results)
        print(f'\nSummary: {os.path.join(REPORT_DIR, "summary.json")}')


if __name__ == '__main__':
    main()
