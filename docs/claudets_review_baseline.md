# claudets 审查基线摘要

本项目当前优先修复方向：

1. 删除明文 Tushare token，改环境变量。
2. 修复 `main.py` / `pipeline.workflow.py` / `evolution.engine.py` 接口不一致。
3. 修复 `factor_id` 重复。
4. 修复 `ExprNode.structure_hash()` 过度简化。
5. 修复因子表达式缺窗口参数。
6. 修复负 IC 因子未反向使用。
7. 修复交易成本乘法扣除问题，改为按 turnover 扣。
8. 删除回撤事后 clip。
9. 修复测试期成交量筛股票池造成的未来信息。
10. 修复周频日期锚点，用真实最后交易日。
11. 改为前复权数据源。
12. `report.md` 拆成已实现 / 部分实现 / 未实现。
13. `report_v*.md` 增加 20 轮整体分布，不只展示最好轮。
14. 新增 long-only TopN 回测，不再把 long-short 当实盘。

任何 Claude 修改都应先围绕这些问题进行，不要优先做表面优化。
