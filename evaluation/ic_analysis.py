"""Spearman Rank IC analysis."""
import numpy as np
import pandas as pd


class ICAnalyzer:
    def __init__(self, factor_values: pd.Series, forward_returns: pd.Series):
        self.factor = factor_values
        self.fwd_ret = forward_returns

    def compute_weekly_ic(self) -> pd.Series:
        combined = pd.DataFrame({"factor": self.factor, "fwd_ret": self.fwd_ret}).dropna()
        if combined.empty:
            return pd.Series(dtype=float, name="IC")
        ic_series = combined.groupby("trade_date").apply(
            lambda group: group["factor"].corr(group["fwd_ret"], method="spearman")
        )
        ic_series.name = "IC"
        return ic_series

    def compute_ic_summary(self) -> dict:
        ic = self.compute_weekly_ic().dropna()
        if len(ic) == 0:
            return {"ic_mean": 0, "ic_ir": 0, "ic_t": 0, "ic_pos_ratio": 0, "ic_std": 0, "n_periods": 0}
        ic_mean = float(ic.mean())
        ic_std = float(ic.std())
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0.0
        ic_t = self._newey_west_tstat(ic)
        return {
            "ic_mean": round(ic_mean, 6),
            "ic_std": round(ic_std, 6),
            "ic_ir": round(ic_ir, 4),
            "ic_t": round(ic_t, 4),
            "ic_pos_ratio": round(float((ic > 0).mean()), 4),
            "n_periods": len(ic),
        }

    def _newey_west_tstat(self, ic_series: pd.Series, max_lag: int = None) -> float:
        n = len(ic_series)
        if n < 3:
            return 0.0
        if max_lag is None:
            max_lag = min(int(4 * (n / 100) ** (2 / 9)), n - 1)
        ic_mean = ic_series.mean()
        demeaned = ic_series - ic_mean
        var = np.sum(demeaned ** 2)
        for lag in range(1, max_lag + 1):
            weight = 1 - lag / (max_lag + 1)
            var += 2 * weight * np.sum(demeaned.iloc[lag:].values * demeaned.iloc[:-lag].values)
        var /= n
        se = np.sqrt(var / n) if var > 0 else np.inf
        return float(ic_mean / se) if se > 0 else 0.0
