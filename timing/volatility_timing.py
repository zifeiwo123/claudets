"""波动率择时信号"""
import numpy as np
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class VolatilityTiming:
    """波动率择时引擎"""

    def __init__(self, market_returns: pd.Series):
        """
        market_returns: pd.Series index=trade_date 市场周收益率
        """
        self.returns = market_returns.dropna()
        self.signal = None

    def compute_signal(self, current_lookback: int = 4,
                       hist_lookback: int = 52,
                       high_threshold: float = 1.5,
                       low_threshold: float = 0.5) -> pd.Series:
        """计算波动率择时信号

        - 当期年化vol > high_threshold * 滚动历史vol → -1 (降仓)
        - 当期年化vol < low_threshold * 滚动历史vol → +1 (加仓)
        - 其他 → 0 (维持)

        Returns:
            pd.Series index=trade_date, values ∈ {-1, 0, 1}
        """
        signals = pd.Series(0, index=self.returns.index, dtype=int)

        for i in range(hist_lookback, len(self.returns)):
            current_vol = self.returns.iloc[i - current_lookback + 1:i + 1].std() * np.sqrt(52)
            hist_vol = self.returns.iloc[i - hist_lookback:i].std() * np.sqrt(52)

            if hist_vol == 0:
                continue

            if current_vol > high_threshold * hist_vol:
                signals.iloc[i] = -1
            elif current_vol < low_threshold * hist_vol:
                signals.iloc[i] = 1

        self.signal = signals
        logger.info(f"波动率择时信号: 降仓={(signals==-1).sum()}期, "
                    f"加仓={(signals==1).sum()}期, 维持={(signals==0).sum()}期")
        return signals

    def apply_to_weights(self, base_weights: pd.DataFrame,
                         signal: pd.Series = None) -> pd.DataFrame:
        """将波动率信号应用于权重调整

        Args:
            base_weights: pd.DataFrame index=trade_date, columns=assets
            signal: 择时信号，-1降仓50%, +1加仓50%, 0不变

        Returns:
            调整后的权重
        """
        if signal is None:
            signal = self.signal
        if signal is None:
            return base_weights

        adjusted = base_weights.copy()
        common_dates = adjusted.index.intersection(signal.index)
        for date in common_dates:
            if signal[date] == -1:
                adjusted.loc[date] *= 0.5
            elif signal[date] == 1:
                adjusted.loc[date] *= 1.5
        return adjusted
