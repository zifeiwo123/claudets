# 给 Claude Code 的任务说明：先做 final diagnosis 口径核查，不要急着执行 Phase 1

> 项目：`claudets`  
> 当前状态：已经完成 `diagnosis_report.md`、`diagnosis_followup.md`、`final_diagnosis_report.md`。  
> 当前目标：**先核查 final diagnosis 的口径一致性，再决定是否执行 Phase 1。**  
> 重要要求：**先不要执行 Phase 1，不要直接改策略，不要继续跑 GP，不要直接切 long-only。**

---

# 1. 背景

目前项目已经从最开始的“工程硬伤修复”，进入到了“研究方向判断”阶段。

已有报告大致形成了这样的结论：

```text
1. 之前 50 轮 clean GP run 全部负 Sharpe。
2. 工程层面的明显硬伤大多已经修复。
3. 简单因子并不是完全没信号。
4. long-only 组合在测试期表现明显好于 long-short。
5. 中盘 / 流动性过滤 universe 的表现好于当前 top400 volume universe。
6. 报告认为 long-short 结构是失败主因。
```

这个方向有价值，但现在还不能直接进入：

```text
Phase 1: long-only + mid-cap universe + IC_IR >= 0.20
```

因为当前几份诊断报告里出现了一些口径矛盾和未解释问题。  
如果这些问题不先核清楚，后面很容易从一个错误的 long-short 方向，跳到一个被牛市 beta 美化的 long-only 方向。

---

# 2. 这次任务的核心目标

本次任务不是开发新策略，而是生成一份新的口径核查报告：

```text
report/final_diagnosis_audit.md
```

目标是回答：

```text
final_diagnosis_report.md 里的结论是否自洽？
long-short 失败的证据链是否一致？
long-only 的高 Sharpe 是否主要来自 beta？
中盘 universe 的收益是否真的有 alpha？
当前 test 期是否已经被用于方向选择？
Phase 1 的验收标准是否应该修改？
```

---

# 3. 严格禁止事项

本次请不要做以下事情：

```text
不要执行 Phase 1
不要直接切换成 long-only 正式策略
不要继续跑新的 GP
不要新增复杂特征
不要改正式策略口径
不要用 test 期结果继续挑参数
不要把 long-only 高 Sharpe 直接当最终策略结论
不要覆盖原有诊断报告
```

本次只做：

```text
口径核查
矛盾解释
补充对照表
风险说明
修改 Phase 1 验收标准
```

---

# 4. 必须核查的第一件事：-volume long-short 一正一负的矛盾

当前报告中有一个最重要的矛盾。

## 4.1 矛盾描述

在 `final_diagnosis_report.md` / `diagnosis_followup.md` 中，实验 A 使用 `-volume` 因子在当前 universe 上拆解时，显示：

```text
Long leg: +41.7% annual, Sharpe +1.63
Short leg: +15.4% annual, Sharpe +0.62
Spread gross: +21.5% annual, Sharpe +1.31
Spread net: +14.9% annual, Sharpe +0.91
```

这说明：

```text
-volume 单因子 long-short spread 是正的，扣成本后仍然为正。
```

但是在单因子 × 组合结构表里，同样的 `-volume` 又显示：

```text
-volume LS Net Sharpe = -0.71
```

IC_IR 阈值网格中，单因子 `-volume` 也显示：

```text
Net Sharpe = -0.71
```

这两个结论不能同时成立。

---

## 4.2 请必须解释的问题

请明确解释：

```text
为什么 -volume 在实验 A 中 net Sharpe 是 +0.91，
但在实验 B / IC_IR grid 中 LS Net Sharpe 是 -0.71？
```

请逐项核查以下口径是否一致：

```text
1. 是否使用同一个日期区间？
2. 是否使用同一个 universe？
3. 是否使用同一个持仓数量？
4. 是否都是 top/bottom 20%？
5. 是否一个是 long-short spread，另一个是 dollar-neutral portfolio？
6. 是否一个用了 direction adjusted factor，另一个没用？
7. 是否一个用了 gross，另一个用了 net？
8. 是否成本扣法一致？
9. 是否权重方式一致？
10. 是否 benchmark / date alignment 影响了指标？
11. 是否有代码 bug？
```

---

## 4.3 必须重新输出统一口径对照表

请新增一张表，统一使用同一个函数、同一个参数、同一个时间区间，重新计算 `-volume` 的 long-short 表现。

保存为：

```text
report/ls_consistency_check.parquet
```

或者：

```text
report/ls_consistency_check.csv
```

表结构建议：

```text
factor
universe
period
portfolio_type
top_pct_or_n
bottom_pct_or_n
weighting
cost_model
direction_used
annual_return
sharpe
max_drawdown
cum_return
turnover
cost
```

至少包含以下组合：

```text
-volume long-only top50
-volume long-only top100
-volume long-short top/bottom 20%
-volume spread gross
-volume spread net
```

并在 `report/final_diagnosis_audit.md` 中解释最终到底哪个数是正确的。

---

# 5. 第二件事：long-only 高 Sharpe 需要补 alpha 口径

当前报告里 long-only 的 Sharpe 很好看，例如：

```text
-ret_4w LO50 Sharpe +2.00
-volume LO50 Sharpe +1.96
中盘 universe LO50 Sharpe 3.4 ~ 3.6
```

但这还不能直接说明策略 alpha 很强。

因为测试期是强 beta 行情，报告自己也提到：

```text
2025-07 以来 A 股强牛市，ChiNext +75.3%
```

所以 long-only 的高 Sharpe 可能有很大一部分来自：

```text
市场 beta
universe beta
中盘 beta
低波动 beta
行业暴露
```

---

## 5.1 必须补充的指标

请对所有 long-only Top50 / Top100 结果补充以下指标：

```text
absolute_annual_return
absolute_sharpe
absolute_max_drawdown

universe_equal_weight_annual_return
excess_annual_return_vs_universe
information_ratio_vs_universe
relative_max_drawdown_vs_universe
weekly_excess_win_rate

hs300_excess_return
cyb_excess_return
if_available_zz500_excess_return
if_available_zz1000_excess_return

turnover
annualized_cost
holding_count
```

如果部分 benchmark 暂时没有数据，例如中证500 / 中证1000，请在报告中写明：

```text
当前缺少 zz500 / zz1000 数据，暂未接入。
```

不要编假数据。

---

## 5.2 必须关注 universe equal-weight

尤其要看：

```text
excess_vs_universe_equal_weight
information_ratio_vs_universe
relative_max_drawdown_vs_universe
```

因为如果策略只是：

```text
绝对收益高
Sharpe 高
但跑不赢自己的 universe 等权
```

那么说明它赚的主要是 universe beta，不是 alpha。

---

## 5.3 保存输出文件

请新增：

```text
report/long_only_alpha_metrics.parquet
```

或：

```text
report/long_only_alpha_metrics.csv
```

建议字段：

```text
universe
factor
period
portfolio_type
top_n
annual_return
sharpe
max_drawdown
universe_ew_annual_return
excess_annual_return
information_ratio
relative_max_drawdown
weekly_excess_win_rate
turnover
annualized_cost
holding_count
```

---

# 6. 第三件事：核查 U2/U3/U4 universe 是否有未来信息

报告中认为：

```text
U2 amount middle 60%
U3 vol*close middle 60%
U4 liquidity filtered
```

显著优于当前 U1 top400 volume。

这可能是对的，但必须确认这些 universe 是用 **train 期信息** 构造，而不是用了 test 期全段信息。

---

## 6.1 必须核查

请检查 `diagnostics/followup_diagnosis.py` 中 universe 构造逻辑，确认：

```text
U1_current_top400_volume 是否只用 train 期信息？
U2_amount_middle_60pct 是否只用 train 期信息？
U3_vol_close_middle_60pct 是否只用 train 期信息？
U4_liquidity_filtered 是否只用 train 期或 t-1 信息？
```

如果用了全样本或 test 期信息，请标为严重问题，并修正为 train-only 或滚动构造。

---

## 6.2 必须输出 universe 构造摘要

请输出：

```text
report/universe_construction_audit.csv
```

字段建议：

```text
universe
construction_field
construction_period
uses_train_only
uses_test_information
stock_count
median_amount
median_volume
median_market_proxy
notes
```

如果没有 total_mv / circ_mv，不要说“中盘市值”，应改称：

```text
中等成交额
中等成交活跃度
中等 vol*close 代理
```

不要把 `volume` 或 `vol*close` 直接等同为真实市值。

---

# 7. 第四件事：test 期已经被用于方向选择，必须写入风险

当前报告已经用 test 期判断了：

```text
long-only 比 long-short 好
U3/U4 比 U1 好
-ret_4w 比其他因子好
IC_IR >= 0.20 更好
```

这意味着当前 test 期已经不再是干净的最终样本外。

---

## 7.1 必须在报告中说明

请在 `report/final_diagnosis_audit.md` 中明确写：

```text
当前 2025-07+ test period 已经被用于诊断和方向选择。
因此，后续 Phase 1 不能继续把同一个 test period 当作最终样本外证明。
```

---

## 7.2 必须提出新的验证方案

请提出至少两种验证方案：

### 方案 A：Walk-forward

例如：

```text
2023H1 train -> 2023H2 validate
2023H2 train -> 2024H1 validate
2024H1 train -> 2024H2 validate
2024H2 train -> 2025H1 validate
2025H1 train -> 2025H2 validate
```

### 方案 B：Final holdout

例如：

```text
train: 2023-2024
validation/development: 2025-01 ~ 2025-12
final_holdout: 2026-01 以后
```

具体区间请根据当前数据可用性调整。

---

# 8. 第五件事：修正 Phase 1 的验收标准

当前报告提出：

```text
Phase 1 完成后，long-only 组合应在测试期产出正 Sharpe >= 0.5
```

这个验收标准太宽，也容易被牛市 beta 满足。

---

## 8.1 新的 Phase 1 验收标准

请将 Phase 1 验收标准改为：

```text
1. long-only Top50 / Top100 在多个切分区间中，相对 universe equal-weight 有正超额；
2. information ratio vs universe equal-weight 为正；
3. 最大相对回撤可接受；
4. 不是只在 2025-07+ 强牛市区间成立；
5. 结果必须同时报告 absolute return 和 excess return；
6. 必须输出持仓换手率和成本；
7. 必须说明是否存在行业 / 市值 / 流动性集中暴露。
```

不要再只用：

```text
absolute Sharpe >= 0.5
```

作为成功标准。

---

# 9. 第六件事：不要急着说 “GP 不是问题”

当前报告说：

```text
GP 不是问题，组合环节才是。
```

这个结论有一定道理，但说得太满。

更严谨的说法应该是：

```text
GP 暂时没有证明有增量价值。
当前最有效的信号仍然是简单人工因子：
-ret_4w、-volume、-vol_4w、-amplitude。
```

---

## 9.1 请在报告中改成更谨慎的表达

请把相关结论改为：

```text
目前 GP 的主要问题不是工程无法运行，而是其产出的复杂因子尚未证明能稳定跑赢 simple baseline。
Phase 1 应先用 simple baseline 验证 long-only + universe 结构。
只有当 simple baseline 在 walk-forward 中有正超额后，才重新启用 GP。
重新启用 GP 时，复杂因子必须证明能跑赢 simple factor baseline，否则不纳入组合。
```

---

# 10. 本次需要生成的文件

本次任务完成后，应至少新增：

```text
report/final_diagnosis_audit.md
report/ls_consistency_check.csv 或 .parquet
report/long_only_alpha_metrics.csv 或 .parquet
report/universe_construction_audit.csv 或 .parquet
```

如果暂时无法生成某些文件，请说明原因，并至少在：

```text
report/final_diagnosis_audit.md
```

里写出：

```text
缺少哪些字段
缺少哪些数据
需要新增哪些函数
下一步如何补齐
```

---

# 11. final_diagnosis_audit.md 推荐结构

请按以下结构生成：

```markdown
# final diagnosis audit:口径核查与 Phase 1 前置审查

## 1. Why this audit is needed

说明当前 final diagnosis 已经有重要方向，但仍有口径矛盾，不能直接执行 Phase 1。

## 2. Long-short consistency check

解释 -volume long-short 一正一负的原因。

必须回答：
- 哪个结果是正确的？
- 为什么之前出现差异？
- 是否是函数、参数、日期、成本、权重、方向不一致？

## 3. Long-only alpha metrics

展示 long-only 绝对收益与相对 universe equal-weight 的超额收益。

必须回答：
- high Sharpe 是否主要来自 beta？
- 有没有稳定 alpha？
- 哪些因子在 alpha 口径下仍然值得保留？

## 4. Universe construction audit

说明 U1/U2/U3/U4 如何构造。

必须回答：
- 是否只用 train 期信息？
- 是否有 test 信息泄漏？
- U3/U4 是否能称为中盘 universe，还是只是成交活跃度 proxy？

## 5. Test period contamination

说明当前 test 期已经被用于方向选择。

必须回答：
- 以后还能不能把 2025-07+ 当 final test？
- 推荐 walk-forward 还是 final holdout？

## 6. Revised Phase 1 acceptance criteria

把验收标准从 absolute Sharpe 改成 excess vs universe + walk-forward。

## 7. Revised conclusion

用更谨慎的语气总结：
- long-only 是更符合项目目标的方向；
- mid-liquidity / mid-activity universe 值得继续；
- 但必须通过 alpha 口径和 walk-forward 继续验证；
- GP 暂时先停，simple baseline 先行。
```

---

# 12. 本次结束时必须汇报

任务结束时，请输出：

```text
1. 读了哪些文件
2. 新增 / 修改了哪些文件
3. 是否运行 python -m compileall -q .
4. 是否生成了 final_diagnosis_audit.md
5. 是否解释清楚 -volume long-short 一正一负
6. U2/U3/U4 是否确认无未来信息
7. long-only 是否在 alpha 口径下仍然成立
8. 是否需要重新跑 walk-forward
9. 下一步建议
```

---

# 13. 最重要的提醒

这次不要急着“执行方案”。

当前正确节奏是：

```text
先核清楚报告矛盾
再确认 long-only 的 alpha 不是 beta
再确认 universe 没有未来信息
再修改 Phase 1 验收标准
最后才进入 Phase 1
```

否则项目会从：

```text
long-short 方向错误
```

跳到：

```text
long-only 被牛市 beta 美化
```

这两个坑都要避开。
