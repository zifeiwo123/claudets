"""Pyfolio封装 - 绩效归因"""
import pandas as pd
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


class PyfolioRunner:
    """Pyfolio绩效归因封装"""

    def __init__(self, returns: pd.Series):
        """
        returns: pd.Series index=trade_date, values=组合收益率
        """
        self.returns = returns.dropna()

    def run(self) -> dict:
        """运行Pyfolio分析"""
        try:
            import pyfolio as pf
        except ImportError:
            logger.warning("pyfolio未安装，跳过绩效归因")
            return {"status": "skipped", "reason": "pyfolio not installed"}

        try:
            returns = self.returns.copy()
            returns.index = pd.to_datetime(returns.index)

            # 生成tear sheet
            # pf.create_full_tear_sheet(returns)

            # 提取关键指标
            if hasattr(pf.timeseries, 'perf_stats'):
                stats = pf.timeseries.perf_stats(returns)
            else:
                stats = self._compute_stats(returns)

            return {"status": "success", "stats": stats}
        except Exception as e:
            logger.error(f"Pyfolio分析失败: {e}")
            return {"status": "error", "reason": str(e)}

    def _compute_stats(self, returns: pd.Series) -> dict:
        """手动计算绩效统计"""
        ann_factor = 52  # 周频年化系数
        cum_ret = (1 + returns).prod() - 1
        ann_ret = (1 + cum_ret) ** (ann_factor / len(returns)) - 1
        ann_vol = returns.std() * np.sqrt(ann_factor)
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0

        # Max Drawdown
        cum = (1 + returns).cumprod()
        peak = cum.expanding().max()
        dd = (cum / peak) - 1
        max_dd = dd.min()

        # Calmar
        calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0

        return {
            "annual_return": round(float(ann_ret), 4),
            "annual_volatility": round(float(ann_vol), 4),
            "sharpe_ratio": round(float(sharpe), 4),
            "max_drawdown": round(float(max_dd), 4),
            "calmar_ratio": round(float(calmar), 4),
            "cumulative_return": round(float(cum_ret), 4),
        }
