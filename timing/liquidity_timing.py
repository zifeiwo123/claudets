"""流动性择时信号"""
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class LiquidityTiming:
    """流动性择时引擎"""

    def __init__(self, market_data: pd.DataFrame):
        """
        market_data: pd.DataFrame index=trade_date, 包含 'volume' 和 'close' 列
                     或直接使用成交额数据
        """
        self.data = market_data
        self.signal = None

    def compute_signal(self, ma_window: int = 20,
                       low_threshold: float = 0.7,
                       high_threshold: float = 1.3) -> pd.Series:
        """计算流动性择时信号

        - 市场成交额 < 20日均值 * 0.7 → -1 (降仓/减仓)
        - 市场成交额 > 20日均值 * 1.3 → +1 (加仓)
        - 其他 → 0 (维持)

        Returns:
            pd.Series index=trade_date, values ∈ {-1, 0, 1}
        """
        # 计算市场总成交额
        if "amount" in self.data.columns:
            turnover = self.data["amount"]
        elif "volume" in self.data.columns and "close" in self.data.columns:
            turnover = self.data["volume"] * self.data["close"]
        else:
            turnover = self.data.iloc[:, 0]

        turnover = turnover.dropna()

        ma = turnover.rolling(ma_window).mean()
        ratio = turnover / ma

        signals = pd.Series(0, index=turnover.index, dtype=int)
        signals[ratio < low_threshold] = -1
        signals[ratio > high_threshold] = 1

        self.signal = signals
        logger.info(f"流动性择时信号: 降仓={(signals==-1).sum()}期, "
                    f"加仓={(signals==1).sum()}期, 维持={(signals==0).sum()}期")
        return signals
