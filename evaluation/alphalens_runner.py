"""Alphalens封装 - 适配周频数据"""
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


class AlphalensRunner:
    """Alphalens因子分析封装"""

    def __init__(self, factor_values: pd.Series, prices: pd.DataFrame):
        """
        factor_values: MultiIndex (trade_date, ts_code) 因子值
        prices: DataFrame index=trade_date, columns=ts_code, values=close price
        """
        self.factor = factor_values
        self.prices = prices

    def run(self, periods=(1, 2, 4)) -> dict:
        """
        运行Alphalens分析，适配周频。
        periods=(1,2,4) 对应1周后、2周后、4周后收益。
        """
        try:
            from alphalens.utils import get_clean_factor_and_forward_returns

            factor_data = get_clean_factor_and_forward_returns(
                factor=self.factor,
                prices=self.prices,
                quantiles=5,
                periods=periods,
                max_loss=0.5,
            )
            logger.info(f"Alphalens因子数据准备完成，shape={factor_data.shape}")

            return {
                "factor_data": factor_data,
                "ic_mean": float(factor_data.groupby("factor_quantile")["1D"].mean().iloc[-1]),
                "status": "success",
            }
        except ImportError:
            logger.warning("alphalens未安装，跳过分析")
            return {"status": "skipped", "reason": "alphalens not installed"}
        except Exception as e:
            logger.error(f"Alphalens分析失败: {e}")
            return {"status": "error", "reason": str(e)}

    def create_full_tear_sheet(self, factor_data=None):
        """生成完整Alphalens报告"""
        try:
            from alphalens.plotting import plot_quantile_returns_bar
            from alphalens.performance import mean_return_by_quantile
        except ImportError:
            logger.warning("alphalens未安装")
            return

        if factor_data is None:
            result = self.run()
            factor_data = result.get("factor_data")

        if factor_data is None:
            return

        # 简化输出：打印各分位均值
        mean_ret_by_q = mean_return_by_quantile(factor_data, by_date=False)
        logger.info(f"各分位前向收益均值:\n{mean_ret_by_q}")
