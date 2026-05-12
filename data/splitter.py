"""数据集划分 - 训练/验证/测试集"""
import pandas as pd
from config.settings import (
    TRAIN_START, TRAIN_END,
    VAL_START, VAL_END,
    TEST_START, WEEKLY_PARQUET,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class DataSplitter:
    """按时间划分训练/验证/测试集"""

    def __init__(self):
        self.train = None
        self.val = None
        self.test = None
        self.weekly = None

    def load_weekly(self, path: str = WEEKLY_PARQUET) -> pd.DataFrame:
        self.weekly = pd.read_parquet(path)
        self.weekly["trade_date"] = pd.to_datetime(self.weekly["trade_date"])
        logger.info(f"加载周频数据: {len(self.weekly)} 条")
        return self.weekly

    def split(self) -> dict:
        """划分三个数据集"""
        df = self.weekly
        self.train = df[
            (df["trade_date"] >= TRAIN_START) & (df["trade_date"] <= TRAIN_END)
        ].copy()
        self.val = df[
            (df["trade_date"] >= VAL_START) & (df["trade_date"] <= VAL_END)
        ].copy()
        self.test = df[
            (df["trade_date"] >= TEST_START)
        ].copy()

        logger.info(f"训练集: {TRAIN_START} ~ {TRAIN_END}, {len(self.train)} 条")
        logger.info(f"验证集: {VAL_START} ~ {VAL_END}, {len(self.val)} 条")
        logger.info(f"测试集: {TEST_START} ~ 至今, {len(self.test)} 条")

        return {"train": self.train, "val": self.val, "test": self.test}
