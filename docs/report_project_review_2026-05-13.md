# claudets report/project review - 2026-05-13

## 结论

当前 `report/report_v68.md` 的效果差，不应简单理解为“因子还不够强”。更关键的问题是研究闭环存在口径偏差，旧报告不能继续作为策略结论使用。

## 主要问题

1. 方案设计问题：项目同时存在 `main.py`、`run_iteration.py`、`autonomous_loop.py` 多个入口，且历史入口里仍有旧成本和风控逻辑，容易造成报告口径漂移。
2. 因子挖掘问题：旧搜索允许裸 `volume`、`amount`、`scale(volume)` 这类规模/流动性暴露进入 top factors，经济含义不稳定，容易把市场结构暴露误当 alpha。
3. 验证集防线失效：因子池保存的是训练集 IC，但后续父代选择、信号方向和测试组合会读取这个结果，导致验证集方向没有真正约束测试组合。
4. 回测成本问题：旧主循环把固定成本按 `0.004 / n_weeks` 摊薄，明显低估交易成本；旧脚本还残留乘法扣成本。
5. 风控问题：旧脚本存在事后 `clip(lower=-0.03)` 裁剪收益的逻辑，这不能作为正式回测口径。
6. 报告治理问题：历史 `report.md` 出现乱码且部分文字宣称“跑赢基准”，与最新 report_v68 的负收益和未实现项不一致。
7. 数据口径问题：当前报告明确写出 forward-adjusted prices(qfq) 未实现，因此所有旧收益只能作为工程流程验证，不能作为 A 股可交易结论。

## 已修复方向

1. 因子池改为保存验证集 IC、方向和 adjusted IC，同时保留训练集 IC 作为诊断字段。
2. 进化引擎使用固定 universe，并与主流程保持 Top 400 口径一致。
3. 因子约束拒绝裸价格/成交量/成交额和简单 identity rescale 作为完整 alpha。
4. 组合成本改为基于换手率扣减：`net_ret = raw_ret - turnover * cost_rate`。
5. 风控波动信号改为使用 `shift(1)` 后的历史收益。
6. 报告 top factors 改为来自最终 evolved pool 的验证集指标，而不是初始评估表。
7. hooks、agents、CLAUDE.md 已恢复为可读规则，并新增验证集 IC、裸因子、成本、clip、密钥等守门项。

## 仍不可用的结论

- `report/report.md` 和旧版 `report_v*.md` 均不能作为修复后的策略结论。
- 任何“跑赢基准”“回撤可控”“因子有效”的陈述，都需要在修复后重新跑实验并重生成 report。
- 在 qfq 数据未接入前，收益数字只能用于工程验证。

## 下一步建议

1. 先统一唯一生产入口，建议以 `autonomous_loop.py` 为准，其余入口降级为开发/旧版脚本或迁移到同一 pipeline。
2. 重新生成周频 qfq 数据和日线特征周末快照后再跑完整实验。
3. 增加 long-only TopN/Top% 组合，与 long-short 研究组合分开报告。
4. 增加 walk-forward 或 final holdout，避免反复看 test 后继续调参。
5. 报告新增 iteration 分布统计，而不只展示单次 iteration。
