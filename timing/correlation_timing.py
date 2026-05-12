"""相关性择时信号 - 剔除高相关因子"""
import numpy as np
import pandas as pd
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger(__name__)


class CorrelationTiming:
    """相关性择时引擎"""

    def __init__(self, factor_values: Dict[str, pd.Series] = None):
        """
        factor_values: {factor_id: pd.Series(MultiIndex date+asset)}
        """
        self.factor_values = factor_values or {}

    def compute_pairwise_corr(self, date: str = None) -> pd.DataFrame:
        """计算因子间滚动Spearman相关矩阵

        如果没有指定日期，使用最新的一期
        """
        if not self.factor_values:
            return pd.DataFrame()

        # 选择最新一期截面
        first_fid = list(self.factor_values.keys())[0]
        dates = self.factor_values[first_fid].index.get_level_values("trade_date").unique()
        if date is None:
            date = dates[-1]

        # 提取各因子的截面值
        df = pd.DataFrame()
        for fid, fs in self.factor_values.items():
            if date in fs.index.get_level_values("trade_date"):
                vals = fs.xs(date, level="trade_date").dropna()
                df[fid] = vals

        if df.empty or df.shape[1] < 2:
            return pd.DataFrame()

        corr_matrix = df.corr(method="spearman")
        return corr_matrix

    def rolling_pairwise_corr(self, window: int = 12) -> pd.DataFrame:
        """滚动计算因子间时间序列IC的相关性

        Returns:
            pd.DataFrame 平均相关系数矩阵
        """
        if len(self.factor_values) < 2:
            return pd.DataFrame()

        # 构建因子收益序列（每期多空收益的交叉）
        fid_list = list(self.factor_values.keys())
        factor_rets = pd.DataFrame()

        for fid in fid_list:
            fs = self.factor_values[fid]
            # 用因子值截面均值的变化率作为因子收益代理
            ts = fs.groupby("trade_date").mean()
            factor_rets[fid] = ts

        if factor_rets.shape[1] < 2:
            return pd.DataFrame()

        return factor_rets.rolling(window).corr(method="spearman")

    def find_redundant_factors(self, corr_threshold: float = 0.7,
                               lookback: int = 8) -> List[str]:
        """找出高相关的冗余因子

        Returns:
            需要剔除的因子ID列表
        """
        if len(self.factor_values) < 2:
            return []

        corr_matrix = self.compute_pairwise_corr()
        if corr_matrix.empty:
            return []

        fid_list = corr_matrix.columns.tolist()
        removed = set()
        to_remove = []

        for i, fid_a in enumerate(fid_list):
            if fid_a in removed:
                continue
            for j in range(i + 1, len(fid_list)):
                fid_b = fid_list[j]
                if fid_b in removed:
                    continue
                if abs(corr_matrix.loc[fid_a, fid_b]) > corr_threshold:
                    # 保留IC更高的那个
                    to_remove.append(fid_b)
                    removed.add(fid_b)
                    logger.info(f"  相关性择时: 剔除 {fid_b} (与 {fid_a} 相关性={corr_matrix.loc[fid_a, fid_b]:.3f})")

        return to_remove

    def compute_adjustment_factors(self) -> pd.Series:
        """计算每个因子的调整系数（0~1）

        Returns:
            pd.Series index=factor_id, values=调整系数
        """
        fid_list = list(self.factor_values.keys())
        adj = pd.Series(1.0, index=fid_list)

        if len(fid_list) < 2:
            return adj

        corr_matrix = self.compute_pairwise_corr()
        if corr_matrix.empty:
            return adj

        for fid in fid_list:
            # 计算该因子与其他因子的平均绝对相关性
            others = [o for o in fid_list if o != fid]
            if others:
                avg_corr = abs(corr_matrix.loc[fid, others]).mean()
                # 若平均相关性>0.7，降低权重
                if avg_corr > 0.7:
                    adj[fid] = max(0.1, 1.0 - (avg_corr - 0.5))
                    logger.info(f"  {fid}: 平均相关性={avg_corr:.3f}, 调整系数={adj[fid]:.2f}")

        return adj
