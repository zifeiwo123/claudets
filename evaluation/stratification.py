"""Quantile stratification checks for factor values."""
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


class StratificationTester:
    def __init__(self, factor_values: pd.Series, forward_returns: pd.Series, n_quantiles: int = 5):
        self.factor = factor_values
        self.fwd_ret = forward_returns
        self.n_quantiles = n_quantiles

    def compute_quantile_returns(self) -> pd.DataFrame:
        combined = pd.DataFrame({"factor": self.factor, "fwd_ret": self.fwd_ret}).dropna()
        if combined.empty:
            return pd.DataFrame()

        def assign_quantile(x):
            return pd.qcut(x, self.n_quantiles, labels=False, duplicates="drop")

        combined["quantile"] = combined.groupby("trade_date")["factor"].transform(assign_quantile)
        if combined["quantile"].isna().all():
            logger.warning("quantile assignment failed")
            return pd.DataFrame()

        quantile_returns = combined.groupby(["trade_date", "quantile"])["fwd_ret"].mean().unstack("quantile")
        quantile_returns.columns = [f"q{int(col) + 1}" for col in quantile_returns.columns]
        return quantile_returns

    def compute_long_short_returns(self) -> pd.Series:
        qr = self.compute_quantile_returns()
        if qr.empty:
            return pd.Series(dtype=float)
        cols = qr.columns.tolist()
        result = qr[cols[-1]] - qr[cols[0]]
        result.name = "long_short"
        return result

    def compute_monotonicity_score(self) -> dict:
        qr = self.compute_quantile_returns()
        if qr.empty:
            return {"monotonicity": 0, "mean_diff": 0, "top_bottom_spread": 0}
        mean_rets = qr.mean().values
        n = len(mean_rets)
        increasing_pairs = sum(1 for i in range(n - 1) if mean_rets[i + 1] > mean_rets[i])
        monotonicity = increasing_pairs / (n - 1) if n > 1 else 0
        return {
            "monotonicity": round(float(monotonicity), 4),
            "mean_diff": round(float(mean_rets[-1] - mean_rets[0]), 6),
            "top_bottom_spread": round(float(qr[qr.columns[-1]].mean() - qr[qr.columns[0]].mean()), 6),
            "quantile_means": {f"q{i + 1}": round(float(mean_rets[i]), 6) for i in range(n)},
        }
