"""Factor computation engine based on trade_date x ts_code pivot matrices."""
import numpy as np
import pandas as pd

from factors.expression_tree import ExprNode
from factors.operators import BASE_FIELDS, FIELDS
from utils.logger import get_logger

logger = get_logger(__name__)


class FactorCompute:
    """Compute expression-tree factors on a fixed stock universe."""

    def __init__(self, data: pd.DataFrame, max_stocks: int = 500, universe: list = None):
        self.raw = data.copy()
        self.raw["trade_date"] = pd.to_datetime(self.raw["trade_date"])
        self.max_stocks = max_stocks

        if universe is not None:
            present = set(self.raw["ts_code"].unique())
            self.stocks = [stock for stock in universe if stock in present]
        else:
            self.stocks = self._select_top_stocks(max_stocks)

        filtered = self.raw[self.raw["ts_code"].isin(self.stocks)]
        self._data = {}
        for field in list(dict.fromkeys(BASE_FIELDS + FIELDS)):
            if field not in filtered.columns:
                continue
            self._data[field] = (
                filtered.pivot_table(index="trade_date", columns="ts_code", values=field, aggfunc="last")
                .sort_index()
            )

        self._data["returns"] = self._data["close"].pct_change(fill_method=None)
        self._data["amplitude"] = (self._data["high"] - self._data["low"]) / self._data["close"]
        logger.info("factor compute initialized: %s dates x %s stocks", len(self._data["close"]), len(self.stocks))

    def _select_top_stocks(self, n: int) -> list:
        vol_col = "volume" if "volume" in self.raw.columns else "vol"
        vol_mean = self.raw.groupby("ts_code")[vol_col].mean().sort_values(ascending=False)
        return vol_mean.head(n).index.tolist()

    def compute(self, factor_node: ExprNode, factor_id: str = None) -> pd.Series:
        code = factor_node.to_python()
        exec_globals = {
            "np": np,
            "pd": pd,
            "_data": self._data,
            "_ts_func": self._ts_func,
            "_ts_rank": self._ts_rank,
            "_ts_corr": self._ts_corr,
        }
        result = eval(code, exec_globals, {})
        if isinstance(result, pd.DataFrame):
            stacked = result.stack(dropna=False)
            stacked.name = factor_id or "factor"
            stacked.index.names = ["trade_date", "ts_code"]
            return stacked
        return result

    def compute_batch(self, factors: dict) -> dict:
        results = {}
        for fid, node in factors.items():
            try:
                results[fid] = self.compute(node, fid)
            except Exception as exc:
                logger.warning("skip factor %s: %s", fid, exc)
        return results

    @staticmethod
    def _ts_func(df: pd.DataFrame, window: int, func: str) -> pd.DataFrame:
        roller = df.rolling(window, min_periods=max(3, window // 3))
        if func == "mean":
            return roller.mean()
        if func == "std":
            return roller.std()
        if func == "min":
            return roller.min()
        if func == "max":
            return roller.max()
        if func == "sum":
            return roller.sum()
        return df

    @staticmethod
    def _ts_rank(df: pd.DataFrame, window: int) -> pd.DataFrame:
        result = pd.DataFrame(np.nan, index=df.index, columns=df.columns)
        arr = df.values
        for i in range(window - 1, len(arr)):
            window_data = arr[i - window + 1:i + 1]
            ranks = (window_data.argsort(axis=0).argsort(axis=0) + 1) / window
            result.iloc[i] = ranks[-1]
        return result

    @staticmethod
    def _ts_corr(a: pd.DataFrame, b: pd.DataFrame, window: int) -> pd.DataFrame:
        result = pd.DataFrame(np.nan, index=a.index, columns=a.columns)
        a_arr = a.values
        b_arr = b.values
        for i in range(window - 1, len(a_arr)):
            wa = a_arr[i - window + 1:i + 1]
            wb = b_arr[i - window + 1:i + 1]
            for j in range(a_arr.shape[1]):
                if np.std(wa[:, j]) > 0 and np.std(wb[:, j]) > 0:
                    corr = np.corrcoef(wa[:, j], wb[:, j])[0, 1]
                    result.iloc[i, j] = corr if not np.isnan(corr) else 0
        return result
