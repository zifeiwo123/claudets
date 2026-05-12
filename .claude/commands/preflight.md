请在执行本次任务前做 preflight 检查。

必须回答：

1. 本次任务属于哪个模块：`data`、`factors`、`evaluation`、`portfolio`、`pipeline`、`report`、`config`、`.claude`。
2. 是否影响数据口径：前复权、真实交易日、`t 周因子 -> t+1 周收益`、train/valid/test、固定 universe。
3. 是否影响“日线特征指导、周频调仓”口径：`daily_ohlcv.parquet` 只读，`weekly_daily_features.parquet` 为可再生成中间结果。
4. 是否影响回测指标：IC、RankIC、分层、long-short、long-only、换手成本、回撤控制。
5. 是否影响 report/summary 输出，是否需要重新跑实验。
6. 准备读取哪些文件、可能修改哪些文件。
7. 如果要执行 Bash，先列出命令、预计写入文件和覆盖风险。

长流程命令如 `python main.py`、`python autonomous_loop.py` 运行前必须说明会写入 `report/` 和可能生成 `data/weekly_daily_features.parquet`。
