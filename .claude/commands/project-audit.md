请针对当前 claudets 项目执行一次全局工程审查。

要求：

1. 优先使用 `project-architect` 从全局工程角度审查。
2. 再参考 `data-contract-steward`、`research-methodology-reviewer`、`backtest-governance-reviewer`、`implementation-quality-reviewer`、`report-governance-reviewer` 的关注点。
3. 先不要修改代码，先给审查结论。
4. 必须覆盖：
   - 工程结构与唯一入口
   - 日线特征指导、周频调仓的数据流
   - 数据契约：qfq、真实交易日、train/valid/test、universe
   - 因子研究：验证集方向、裸价格/成交量因子、过拟合
   - 回测治理：成本、换手、风控、benchmark、long-short/long-only
   - 报告治理：summary/report/图表一致性
   - hooks/agents/commands 是否匹配当前程序
5. 结尾给出最应该先做的 5 件事。
