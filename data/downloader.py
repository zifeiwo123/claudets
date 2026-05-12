"""Tushare data downloader.

Default price contract is qfq (forward-adjusted) bars. Raw source files remain
generated artifacts and are ignored by git.
"""
import pandas as pd
import tushare as ts

from config.settings import DATA_END, DATA_START, DAILY_PARQUET, PRICE_ADJUST, TUSHARE_TOKEN
from utils.logger import get_logger

logger = get_logger(__name__)


class DailyDownloader:
    """Download A-share daily OHLCV data from Tushare."""

    def __init__(self):
        if not TUSHARE_TOKEN:
            raise ValueError("Set TUSHARE_TOKEN in the environment before downloading data.")
        ts.set_token(TUSHARE_TOKEN)
        self.pro = ts.pro_api()

    def fetch_daily(self) -> pd.DataFrame:
        """Fetch qfq daily OHLCV data and save to DAILY_PARQUET."""
        logger.info("fetching %s daily bars from Tushare", PRICE_ADJUST)
        all_data = []
        stock_list = self._get_stock_list()

        for i, ts_code in enumerate(stock_list):
            try:
                df = ts.pro_bar(
                    pro_api=self.pro,
                    ts_code=ts_code,
                    start_date=DATA_START,
                    end_date=DATA_END,
                    adj=PRICE_ADJUST,
                    freq="D",
                )
                if df is not None and not df.empty:
                    keep = [col for col in ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"] if col in df.columns]
                    all_data.append(df[keep])
            except Exception as exc:
                logger.warning("skip %s: %s", ts_code, exc)

            if (i + 1) % 500 == 0:
                logger.info("downloaded %s/%s stocks", i + 1, len(stock_list))

        if not all_data:
            raise RuntimeError("No daily bars downloaded.")

        result = pd.concat(all_data, ignore_index=True)
        result["trade_date"] = pd.to_datetime(result["trade_date"])
        result = result.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
        result.to_parquet(DAILY_PARQUET, index=False)
        logger.info("saved daily bars to %s, rows=%s", DAILY_PARQUET, len(result))
        return result

    def _get_stock_list(self) -> list:
        df = self.pro.stock_basic(exchange="", list_status="L", fields="ts_code")
        df = df[~df["ts_code"].str.startswith("8")]
        df = df[~df["ts_code"].str.startswith("4")]
        return df["ts_code"].tolist()
