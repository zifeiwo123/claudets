"""数据预处理器 - 停牌填充、异常值截尾、日频→周频重采样"""
import pandas as pd
import numpy as np
from config.settings import DAILY_PARQUET, WEEKLY_PARQUET
from utils.logger import get_logger

logger = get_logger(__name__)


class Preprocessor:
    """数据清洗与重采样"""

    def __init__(self):
        self.daily = None
        self.weekly = None

    def load_daily(self, path: str = DAILY_PARQUET) -> pd.DataFrame:
        self.daily = pd.read_parquet(path)
        self.daily["trade_date"] = pd.to_datetime(self.daily["trade_date"])
        logger.info(f"加载日K数据: {len(self.daily)} 条")
        return self.daily

    def clean(self) -> pd.DataFrame:
        """清洗日频数据：停牌填充 + 异常值截尾"""
        df = self.daily.copy()
        df = df.sort_values(["ts_code", "trade_date"])

        # 1. 停牌填充（前向填充，最大5日）
        df["volume"] = df.groupby("ts_code")["vol"].transform(
            lambda x: x.replace(0, np.nan).ffill(limit=5)
        )
        df["volume"] = df["volume"].fillna(0)
        price_cols = ["open", "high", "low", "close"]
        for col in price_cols:
            df[col] = df.groupby("ts_code")[col].transform(
                lambda x: x.replace(0, np.nan).ffill(limit=5)
            )
            df[col] = df.groupby("ts_code")[col].transform(
                lambda x: x.fillna(method="bfill", limit=5)
            )

        # 2. 异常值截尾（5σ），基于涨跌幅
        df["ret"] = df.groupby("ts_code")["close"].pct_change()
        df["ret"] = df.groupby("ts_code")["ret"].transform(
            lambda x: x.clip(lower=x.mean() - 5 * x.std(), upper=x.mean() + 5 * x.std())
        )

        self.daily = df
        logger.info(f"日频数据清洗完成: {len(df)} 条")
        return self.daily

    def to_weekly(self) -> pd.DataFrame:
        """日频→周频重采样（周五锚点）"""
        df = self.daily.copy()
        # Task 9: Use last real trade date as weekly anchor (not period start_time)
        df["week_period"] = df["trade_date"].dt.to_period("W-FRI")

        last_trade_dates = df.groupby(["ts_code", "week_period"])["trade_date"].max().reset_index()
        last_trade_dates.columns = ["ts_code", "week_period", "last_trade_date"]

        weekly = df.groupby(["ts_code", "week_period"]).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("vol", "sum"),
            amount=("amount", "sum"),
        ).reset_index()

        weekly = weekly.merge(last_trade_dates, on=["ts_code", "week_period"])

        # Filter weeks with fewer than 3 trading days
        daily_counts = df.groupby(["ts_code", "week_period"]).size().reset_index()
        daily_counts.columns = ["ts_code", "week_period", "n_days"]
        valid_weeks = daily_counts[daily_counts["n_days"] >= 3]

        weekly = weekly.merge(valid_weeks, on=["ts_code", "week_period"], how="inner")

        # Now rename: use last trade date as the weekly date
        weekly = weekly.drop(columns=["week_period"])
        weekly = weekly.rename(columns={"last_trade_date": "trade_date"})
        weekly = weekly.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)

        weekly.to_parquet(WEEKLY_PARQUET, index=False)
        self.weekly = weekly
        logger.info(f"周频数据重采样完成: {len(weekly)} 条，已保存至 {WEEKLY_PARQUET}")
        return self.weekly
