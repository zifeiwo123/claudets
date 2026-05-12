"""Historical-information drawdown governance helpers.

This module is intentionally conservative. It does not clip historical returns
or rewrite realized losses. Any scaling decision is based on information that
would have been visible before the current period.
"""
from typing import Dict

import numpy as np
import pandas as pd

from config.settings import (
    DRAWDOWN_MAX_ITERATIONS,
    DRAWDOWN_WORSEN_STOP_ROUNDS,
    MAX_DRAWDOWN_THRESHOLD,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class DrawdownController:
    """Check drawdown and apply simple historical volatility de-risking."""

    def __init__(
        self,
        portfolio_returns: pd.Series,
        factor_contributions: Dict[str, pd.Series] = None,
        market_data: pd.DataFrame = None,
    ):
        self.returns = portfolio_returns.dropna().copy()
        self.factor_contributions = factor_contributions or {}
        self.market_data = market_data

    def check_drawdown(self) -> Dict:
        if self.returns.empty:
            return {"max_drawdown": 0.0, "breached": False}
        cum = (1 + self.returns).cumprod()
        dd = cum / cum.cummax() - 1
        max_dd = float(dd.min())
        return {"max_drawdown": max_dd, "breached": max_dd < -MAX_DRAWDOWN_THRESHOLD}

    def run(self) -> Dict:
        check = self.check_drawdown()
        if not check["breached"]:
            return {
                "max_drawdown": check["max_drawdown"],
                "passed": True,
                "stages_executed": [],
                "final_returns": self.returns,
                "message": "drawdown is within threshold",
            }

        stages_executed = []
        consecutive_worsen = 0
        previous_mdd = check["max_drawdown"]

        for iteration in range(DRAWDOWN_MAX_ITERATIONS):
            logger.info("drawdown control iteration %s/%s", iteration + 1, DRAWDOWN_MAX_ITERATIONS)

            if len(self.factor_contributions) > 3:
                removed = self._stage_a_remove_recent_negative()
                if removed:
                    stages_executed.append("A_remove_recent_negative")

            if self.market_data is not None:
                scaled = self._stage_b_historical_vol_timing()
                if scaled:
                    stages_executed.append("B_historical_vol_timing")

            # Stage C is deliberately not a fake implementation. Keep a marker
            # only when a caller supplies a real optimizer in the future.
            self._stage_c_not_implemented()

            new_check = self.check_drawdown()
            new_mdd = new_check["max_drawdown"]
            if new_mdd < previous_mdd:
                consecutive_worsen += 1
            else:
                consecutive_worsen = 0
            previous_mdd = new_mdd

            if consecutive_worsen >= DRAWDOWN_WORSEN_STOP_ROUNDS or not new_check["breached"]:
                break

        final_check = self.check_drawdown()
        return {
            "max_drawdown": final_check["max_drawdown"],
            "passed": not final_check["breached"],
            "stages_executed": stages_executed,
            "final_returns": self.returns,
            "message": f"drawdown control finished; MaxDD={final_check['max_drawdown']:.2%}",
        }

    def _stage_a_remove_recent_negative(self) -> list:
        removed = []
        for fid, contribution in list(self.factor_contributions.items()):
            recent = contribution.dropna().tail(4)
            if len(recent) >= 2 and recent.mean() < 0:
                removed.append(fid)
                del self.factor_contributions[fid]
        if removed:
            logger.info("removed recent negative contributors: %s", removed)
        return removed

    def _stage_b_historical_vol_timing(self) -> bool:
        market_ret = self._market_returns()
        if market_ret.empty or len(market_ret) < 20:
            return False

        rolling_vol = market_ret.shift(1).rolling(12, min_periods=6).std() * np.sqrt(52)
        hist_vol = rolling_vol.shift(1).rolling(52, min_periods=12).mean()
        vol_spike = (rolling_vol > 1.5 * hist_vol).reindex(self.returns.index).fillna(False)
        if not vol_spike.any():
            return False

        scale = pd.Series(1.0, index=self.returns.index)
        scale.loc[vol_spike] = 0.5
        self.returns = self.returns * scale
        return True

    def _market_returns(self) -> pd.Series:
        if self.market_data is None:
            return pd.Series(dtype=float)
        if isinstance(self.market_data, pd.Series):
            return self.market_data.pct_change(fill_method=None).dropna()
        if "close" in self.market_data.columns:
            return self.market_data["close"].pct_change(fill_method=None).dropna()
        numeric = self.market_data.select_dtypes(include="number")
        if numeric.empty:
            return pd.Series(dtype=float)
        return numeric.iloc[:, 0].pct_change(fill_method=None).dropna()

    def _stage_c_not_implemented(self) -> None:
        logger.info("stage C risk-parity/max-drawdown optimizer is not implemented in this controller")
