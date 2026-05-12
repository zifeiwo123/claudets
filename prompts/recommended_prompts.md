# 推荐给 Claude Code 的提示词

## 1. 全项目审查

```text
请按 CLAUDE.md 的五步流程审查当前项目：
1）quant-strategy-reviewer 看方案和因子逻辑；
2）backtest-integrity-reviewer 看回测未来函数、成本、股票池、日期锚点；
3）code-hardening-reviewer 看程序是否能跑、接口是否一致；
4）report-consistency-reviewer 看所有 report.md 和 summary 是否一致；
5）fix-implementation-planner 汇总成补丁计划。
先不要修改代码，先给我审查结论和修改顺序。
```

## 2. 直接进入 P0/P1 修复

```text
请按照 CLAUDE.md 的优先级开始修复。先修 P0/P1：删除明文 token、修 main/workflow/engine 接口、修 factor_id 重复、修 structure_hash。每改完一组，运行 python -m compileall . 检查。
```

## 3. 回测可信度专项修复

```text
请调用 backtest-integrity-reviewer 先复查，然后修复：负 IC 因子方向、交易成本扣法、股票池未来信息、周频日期锚点、回撤 clip。修复时不要改变其他无关逻辑。
```

## 4. 报告专项修复

```text
请调用 report-consistency-reviewer 检查 report/report.md、report/report_v*.md、summary.json、factor_evals.csv，然后重写 report.md 的结构：已实现、部分实现、未实现、long-short、long-only、20轮稳定性、风险与局限。
```

## 5. 防止它乱改

```text
你只允许修改这次任务明确相关的文件。不要重构整个项目，不要删除已有报告，不要改数据文件。所有回测口径变化必须写入 changelog 或 report 口径说明。
```

## 6. 让它自动使用多个 agent

```text
请先按 CLAUDE.md 自动选择对应 subagent 完成审查，再由 fix-implementation-planner 汇总计划。没有完成审查前，不要直接改代码。
```

## 7. 改完后让它自检

```text
请完成本轮修改后执行：
python -m compileall .
然后列出：
1）修改了哪些文件；
2）修复了哪些硬伤；
3）哪些问题还没修；
4）是否需要重跑回测；
5）下一步建议。
```
