"""Build daily-derived factor features sampled at weekly rebalance dates.

The trading cadence stays weekly. Daily bars are used only to form features
available at each week's last real trading day, then next-week returns remain
computed from weekly closes.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from config.settings import DAILY_FEATURE_WEEKLY_PARQUET, DAILY_PARQUET, WEEKLY_PARQUET


DAILY_FEATURE_COLUMNS = [
    "d_ret_5d",
    "d_ret_20d",
    "d_vol_20d",
    "d_downside_vol_20d",
    "d_range_20d",
    "d_intraday_strength_5d",
    "d_volume_z20",
    "d_amount_z20",
]


class DailyFeatureBuilder:
    """Create daily rolling features and sample them onto weekly dates."""

    def __init__(
        self,
        daily_path: str = DAILY_PARQUET,
        weekly_path: str = WEEKLY_PARQUET,
        output_path: str = DAILY_FEATURE_WEEKLY_PARQUET,
    ):
        self.daily_path = daily_path
        self.weekly_path = weekly_path
        self.output_path = output_path

    def build(self) -> pd.DataFrame:
        daily = pd.read_parquet(self.daily_path)
        weekly = pd.read_parquet(self.weekly_path)
        return self.build_from_frames(daily, weekly)

    def build_from_frames(self, daily: pd.DataFrame, weekly: pd.DataFrame) -> pd.DataFrame:
        daily = self._normalize_daily(daily)
        weekly = weekly.copy()
        weekly["trade_date"] = pd.to_datetime(weekly["trade_date"])

        features = self._compute_daily_features(daily)
        weekly_keys = weekly[["ts_code", "trade_date"]].drop_duplicates()
        sampled = weekly_keys.merge(features, on=["ts_code", "trade_date"], how="left")

        result = weekly.merge(sampled, on=["ts_code", "trade_date"], how="left")
        result = result.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)

        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        result.to_parquet(self.output_path, index=False)
        return result

    def _normalize_daily(self, daily: pd.DataFrame) -> pd.DataFrame:
        df = daily.copy()
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        if "volume" not in df.columns and "vol" in df.columns:
            df["volume"] = df["vol"]
        needed = ["ts_code", "trade_date", "open", "high", "low", "close", "volume", "amount"]
        missing = [col for col in needed if col not in df.columns]
        if missing:
            raise ValueError(f"daily data missing columns: {missing}")
        return df[needed].sort_values(["ts_code", "trade_date"])

    def _compute_daily_features(self, daily: pd.DataFrame) -> pd.DataFrame:
        df = daily.copy()
        grouped = df.groupby("ts_code", group_keys=False)

        df["daily_ret"] = grouped["close"].transform(lambda x: x.pct_change(fill_method=None))
        df["d_ret_5d"] = grouped["close"].transform(lambda x: x.pct_change(5, fill_method=None))
        df["d_ret_20d"] = grouped["close"].transform(lambda x: x.pct_change(20, fill_method=None))
        df["d_vol_20d"] = grouped["daily_ret"].transform(lambda x: x.rolling(20, min_periods=10).std())
        df["d_downside_vol_20d"] = grouped["daily_ret"].transform(
            lambda x: x.clip(upper=0).rolling(20, min_periods=10).std()
        )
        daily_range = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)
        df["d_range_20d"] = daily_range.groupby(df["ts_code"]).transform(
            lambda x: x.rolling(20, min_periods=10).mean()
        )
        intraday_strength = (df["close"] - df["open"]) / (df["high"] - df["low"]).replace(0, np.nan)
        df["d_intraday_strength_5d"] = intraday_strength.groupby(df["ts_code"]).transform(
            lambda x: x.rolling(5, min_periods=3).mean()
        )
        df["d_volume_z20"] = grouped["volume"].transform(self._rolling_zscore)
        df["d_amount_z20"] = grouped["amount"].transform(self._rolling_zscore)

        return df[["ts_code", "trade_date", *DAILY_FEATURE_COLUMNS]]

    @staticmethod
    def _rolling_zscore(values: pd.Series) -> pd.Series:
        mean = values.rolling(20, min_periods=10).mean()
        std = values.rolling(20, min_periods=10).std()
        return (values - mean) / (std + 1e-10)


def ensure_weekly_daily_features(force: bool = False) -> pd.DataFrame:
    output = Path(DAILY_FEATURE_WEEKLY_PARQUET)
    if output.exists() and not force:
        df = pd.read_parquet(output)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        return df
    return DailyFeatureBuilder().build()
