请根据当前项目生成运行手册。

要求：

1. 梳理主要入口：当前 canonical 入口是 `main.py`，它委托到 `autonomous_loop.py`。
2. 区分轻量检查、特征生成、全量实验、报告查看。
3. 标注每类命令可能写入哪些文件：
   - `data/weekly_daily_features.parquet`
   - `report/report_v*.md`
   - `report/report_v*_chart.png`
   - `report/summary.json`
   - `report/iteration_summary.csv`
   - `report/elite_pool.json`
4. 标注哪些命令需要用户确认后再跑。
5. 给出 Windows PowerShell 示例。
6. 不要擅自实际运行全量回测。
