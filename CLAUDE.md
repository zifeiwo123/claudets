# CLAUDE.md - claudets 工程治理版

本项目定位为 **A 股周频自动 Alpha 因子研究平台**。目标是维护一个可复现、可解释、可扩展的研究工程，不是把某一次回测收益调好看。

## 工作前检查

涉及代码或报告修改前，先判断：

1. 任务属于哪个模块。
2. 是否影响数据口径、复权、交易日、收益对齐或股票池。
3. 是否影响 IC、分层、long-short、long-only、成本、换手或回撤指标。
4. 是否影响 report/summary 输出。
5. 是否需要重新跑实验。

## 数据口径

- A 股价格默认优先使用前复权行情。若当前数据不是 qfq，报告必须明确写成“未前复权，结论仅供工程验证”。
- 周频 `trade_date` 必须是该周最后一个真实交易日，不允许落在周六/周日。
- 默认范式是 `t 周因子 -> t+1 周持有收益`。
- 调仓可以是周频，但信号应优先支持日线级别特征：先在日线上计算滚动收益、波动、量价、日内强弱等特征，再在每周最后一个真实交易日取快照用于周频组合。
- 日线源数据仍只读；日线特征周末快照写入独立中间表，例如 `weekly_daily_features.parquet`。
- universe 不得偷看未来。优先用 train 期确定固定股票池，valid/test 沿用。
- 源数据、原始数据库、parquet 行情默认只读。实验结果写入 `report/` 或独立结果库。

## 因子研究

- 因子表达式必须可复现，报告中要显示字段、算子、窗口参数和左右子树。
- 禁止把裸 `open/high/low/close/volume/amount` 或简单 `scale(volume)` 当作 alpha。它们通常只是价格水平、规模或流动性暴露。
- 鼓励在日线特征字段上做表达式搜索，例如 `d_ret_20d`、`d_vol_20d`、`d_volume_z20`、`d_intraday_strength_5d`，但仍必须经过 train/valid/test 与方向治理。
- 负 IC 因子必须记录 `raw_ic`、`direction`、`adjusted_ic`，组合排序使用方向调整后的信号。
- 父代选择、组合筛选和测试集信号方向必须以验证集指标为准，不能用训练集 IC 代替。
- 多轮自动搜索必须报告整体分布，不能只展示最好 iteration。

## 回测治理

- long-short 与 long-only 必须分开。top 20% long / bottom 20% short 只能称为 long-short 因子研究组合。
- 成本按换手扣：`net_ret = raw_ret - turnover * cost_rate`。不允许 `raw_ret * (1-cost)`。
- 回撤控制只能用历史可见信息，例如 `returns.shift(1).rolling(...)`。不允许事后 `clip(lower=...)` 裁剪历史收益。
- benchmark 日期必须和策略收益日期对齐，并在报告中说明对齐方式。

## 报告规范

主报告必须区分：

- 已实现
- 部分实现
- 未实现
- 实验结果
- 风险与局限
- 下一步计划

报告数字必须来自统一结果源，例如 `summary.json`、`iteration_summary.csv`、`backtest_result.parquet`。若代码修复了研究口径，旧 report 不能继续当作有效策略结论，必须重新跑实验生成新报告。

## 完成定义

每轮结束前说明：

- 修改了哪些文件。
- 为什么这样改。
- 跑了哪些语法检查或测试。
- 是否需要重跑回测/report。
- 哪些结论仍不能使用。
- 下一步建议。
