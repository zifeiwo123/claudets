"""按市值分档的交易滑点模型（替代手续费）"""
import numpy as np
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

# 市值分档与单侧滑点
SLIPPAGE_TIERS = [
    (0.10, 0.0005),  # Top 10% 大市值: 0.05%
    (0.30, 0.0010),  # 10%-30% 中大市值: 0.10%
    (0.50, 0.0015),  # 30%-50% 中等市值: 0.15%
    (0.80, 0.0020),  # 50%-80% 中小市值: 0.20%
    (1.00, 0.0025),  # Bottom 20% 小市值: 0.25%
]


class SlippageModel:
    """按市值分档的交易滑点模型"""

    def __init__(self, market_caps: pd.Series = None):
        """
        market_caps: pd.Series index=ts_code, 各股票的最新市值（或每期市值）
                     如果未提供，默认使用最低档 0.2% 单侧滑点
        """
        self.market_caps = market_caps
        self._tier_map = None

    def fit(self, market_caps: pd.Series):
        """根据市值分档"""
        self.market_caps = market_caps.dropna()
        thresholds = self.market_caps.quantile([t[0] for t in SLIPPAGE_TIERS])
        self._tier_map = {}
        for (pct, rate), threshold in zip(SLIPPAGE_TIERS, thresholds):
            self._tier_map[threshold] = rate
        logger.info(f"滑点分档完成，共 {len(self.market_caps)} 只股票")

    def get_slippage(self, ts_code: str) -> float:
        """获取单只股票的单侧滑点"""
        if self.market_caps is None or ts_code not in self.market_caps.index:
            return 0.002  # 默认 0.2%
        cap = self.market_caps[ts_code]
        for (pct, rate) in SLIPPAGE_TIERS:
            threshold = self.market_caps.quantile(pct)
            if cap <= threshold:
                return rate
        return SLIPPAGE_TIERS[-1][1]

    def get_slippage_series(self, ts_codes: pd.Index) -> pd.Series:
        """批量获取单侧滑点"""
        if self.market_caps is None:
            return pd.Series(0.002, index=ts_codes)
        common = ts_codes.intersection(self.market_caps.index)
        rates = pd.Series(0.002, index=ts_codes)
        for code in common:
            rates[code] = self.get_slippage(code)
        return rates

    def compute_turnover_cost(self, turnover: pd.DataFrame) -> pd.Series:
        """计算每期交易滑点成本

        Args:
            turnover: pd.DataFrame index=trade_date, columns=asset
                      每期每只股票的交易量（买入+卖出金额的0.5倍即换手额）

        Returns:
            pd.Series index=trade_date, 每期的滑点成本
        """
        slippage_map = self.get_slippage_series(turnover.columns)
        costs = turnover.abs().mul(slippage_map * 2)  # 往返 = 单侧 × 2
        return costs.sum(axis=1)

    def compute_cost_from_weights(self, prev_weights: pd.Series,
                                  curr_weights: pd.Series) -> float:
        """基于权重变化计算单期交易滑点成本

        Args:
            prev_weights: 上期持仓权重
            curr_weights: 当期目标权重

        Returns:
            当期滑点成本（已扣除的收益部分）
        """
        turnover_amount = (curr_weights - prev_weights).abs()
        slippage_map = self.get_slippage_series(turnover_amount.index)
        # 往返成本：单侧×2
        cost = (turnover_amount * slippage_map * 2).sum()
        return float(cost)
