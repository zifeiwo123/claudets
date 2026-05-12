"""Portfolio weighting schemes for long-short factor research."""
from typing import Dict

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


class WeightSchemes:
    """Build long-short portfolio returns from factor signals."""

    def __init__(self, factor_signals: Dict[str, pd.Series], forward_returns: pd.Series):
        self.factor_signals = factor_signals
        self.fwd_ret = forward_returns
        self.last_turnover = pd.Series(dtype=float)

    def equal_weight(self) -> pd.Series:
        weights = {fid: 1.0 / max(len(self.factor_signals), 1) for fid in self.factor_signals}
        return self._weighted_portfolio(weights)

    def icir_weight(self, ic_results: Dict[str, dict]) -> pd.Series:
        weights = {}
        for fid in self.factor_signals:
            ic = ic_results.get(fid, {})
            weights[fid] = max(abs(ic.get("ic_ir", 0)), 0.01)
        total = sum(weights.values()) or 1.0
        weights = {fid: value / total for fid, value in weights.items()}
        logger.info("ICIR weights: %s", weights)
        return self._weighted_portfolio(weights)

    def rolling_regression_weight(self, lookback: int = 12) -> pd.Series:
        raise NotImplementedError("rolling_regression_weight is not implemented; use equal_weight or icir_weight")

    def max_sharpe_weight(self) -> pd.Series:
        raise NotImplementedError("max_sharpe_weight is not implemented; use equal_weight or icir_weight")

    def _weighted_portfolio(self, factor_weights: Dict[str, float]) -> pd.Series:
        all_dates = sorted({
            date
            for fs in self.factor_signals.values()
            for date in fs.index.get_level_values("trade_date").unique()
        })

        returns = []
        turnover_records = []
        prev_positions = None

        for date in all_dates:
            signals = {}
            for fid, fs in self.factor_signals.items():
                if date not in fs.index.get_level_values("trade_date"):
                    continue
                sig = fs.xs(date, level="trade_date").dropna()
                if len(sig) > 1:
                    signals[fid] = (sig - sig.mean()) / (sig.std() + 1e-10)

            if not signals:
                continue

            combined = None
            for fid, sig in signals.items():
                weighted = sig * factor_weights.get(fid, 0.0)
                combined = weighted if combined is None else combined.add(weighted, fill_value=0.0)
            combined = combined.dropna()
            if len(combined) < 5:
                continue

            top_n = max(1, len(combined) // 5)
            long_assets = combined.nlargest(top_n).index
            short_assets = combined.nsmallest(top_n).index

            positions = pd.Series(0.0, index=combined.index)
            positions.loc[long_assets] = 1.0 / top_n
            positions.loc[short_assets] = -1.0 / top_n

            turnover = self._compute_turnover(positions, prev_positions)
            prev_positions = positions.copy()

            if date not in self.fwd_ret.index.get_level_values("trade_date"):
                continue
            ret = self.fwd_ret.xs(date, level="trade_date")
            common = positions.index.intersection(ret.index)
            if len(common) == 0:
                continue
            returns.append({"trade_date": date, "return": float((positions[common] * ret[common]).sum())})
            turnover_records.append({"trade_date": date, "turnover": turnover})

        self.last_turnover = self._records_to_series(turnover_records, "turnover")
        return self._records_to_series(returns, "return")

    @staticmethod
    def _compute_turnover(positions: pd.Series, prev_positions: pd.Series = None) -> float:
        if prev_positions is None:
            prev_positions = pd.Series(0.0, index=positions.index)
        idx = positions.index.union(prev_positions.index)
        current = positions.reindex(idx).fillna(0.0)
        previous = prev_positions.reindex(idx).fillna(0.0)
        return float(0.5 * (current - previous).abs().sum())

    @staticmethod
    def _records_to_series(records: list, value_col: str) -> pd.Series:
        if not records:
            return pd.Series(dtype=float)
        return pd.DataFrame(records).set_index("trade_date")[value_col]
