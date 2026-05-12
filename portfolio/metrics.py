"""Weekly portfolio performance metrics."""
import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

ANN_FACTOR = 52


class PerformanceMetrics:
    def __init__(self, returns: pd.Series, weights_history: pd.DataFrame = None):
        self.returns = returns.dropna()
        self.weights = weights_history

    def compute_all(self) -> dict:
        ann_ret = self.annual_return()
        ann_vol = self.annual_volatility()
        sharpe = self.sharpe_ratio()
        max_dd = self.max_drawdown()
        calmar = self.calmar_ratio()
        weekly_win_rate = self.weekly_win_rate()
        monthly_win_rate = self.monthly_win_rate()
        turnover = self.turnover() if self.weights is not None else None
        cumulative = self.cumulative_return()
        logger.info("metrics ann_ret=%.2f%% sharpe=%.2f max_dd=%.2f%%", ann_ret * 100, sharpe, max_dd * 100)
        return {
            "annual_return": round(ann_ret, 4),
            "annual_volatility": round(ann_vol, 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_dd, 4),
            "calmar_ratio": round(calmar, 4),
            "weekly_win_rate": round(weekly_win_rate, 4),
            "monthly_win_rate": round(monthly_win_rate, 4),
            "turnover": round(turnover, 4) if turnover is not None else None,
            "cumulative_return": round(cumulative, 4),
            "total_periods": len(self.returns),
        }

    def annual_return(self) -> float:
        n_periods = len(self.returns)
        if n_periods == 0:
            return 0.0
        cum_ret = (1 + self.returns).prod()
        return float(cum_ret ** (ANN_FACTOR / n_periods) - 1)

    def annual_volatility(self) -> float:
        return float(self.returns.std() * np.sqrt(ANN_FACTOR)) if len(self.returns) > 1 else 0.0

    def sharpe_ratio(self) -> float:
        ann_vol = self.annual_volatility()
        return float(self.annual_return() / ann_vol) if ann_vol > 0 else 0.0

    def max_drawdown(self) -> float:
        if self.returns.empty:
            return 0.0
        cum = (1 + self.returns).cumprod()
        dd = cum / cum.cummax() - 1
        return float(dd.min())

    def calmar_ratio(self) -> float:
        max_dd = self.max_drawdown()
        return float(self.annual_return() / abs(max_dd)) if max_dd != 0 else 0.0

    def cumulative_return(self) -> float:
        return float((1 + self.returns).prod() - 1) if not self.returns.empty else 0.0

    def weekly_win_rate(self) -> float:
        return float((self.returns > 0).mean()) if not self.returns.empty else 0.0

    def monthly_win_rate(self) -> float:
        if len(self.returns) < 4:
            return self.weekly_win_rate()
        monthly = self.returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        return float((monthly > 0).mean()) if not monthly.empty else 0.0

    def turnover(self) -> float:
        if self.weights is None or self.weights.empty:
            return 0.0
        changes = self.weights.diff().abs().sum(axis=1) / 2
        return float(changes.mean())
