# 给 Claude Code 的任务说明：先做 claudets 失败来源拆解，不要继续盲目炼丹

> 项目：`claudets`  
> 当前目标：不是继续追求更高 Sharpe，而是先搞清楚为什么 50 轮 clean run 仍然没有正 alpha。  
> 任务性质：研究诊断 / 失败来源拆解 / 工程化实验设计。  
> 重要要求：**先不要新增复杂 GP 特征，不要继续跑大规模进化，不要急着改成新策略。**

---

# 1. 背景

这个项目是一个 A 股周频自动 Alpha 因子研究 / 回测 / 报告生成工程。

前面已经做过一轮比较大的工程修正，之前那些明显硬伤大多已经处理了，例如：

```text
qfq 前复权价格支持
真实周频交易日
日频派生特征快照
train / val / test 切分
固定 universe
表达式树 GP
约束搜索空间，不再直接使用 raw OHLCV / volume / amount
验证集 IC 方向翻转
按 turnover 扣交易成本
去掉事后 clip 回撤
ts_corr 向量化
stagnation detection
incremental summary save
```

当前 `diagnosis_report.md` 里显示：

```text
Experiment 1:
- 166 iterations
- Sharpe 全负
- best Sharpe -0.64
- mean Sharpe -1.66
- 主要问题是旧搜索空间被 volume / amount 之类表达式污染

Experiment 2:
- commit 887ee89
- 50 iterations clean run
- Sharpe 全负
- best Sharpe -1.46
- mean Sharpe -2.39
- 搜索空间已经更干净
- 速度约 20s / iteration
```

报告中还手工验证了几个简单因子，它们的 IC 方向是正的，但很弱：

```text
1w reversal (-ret_1w)
4w reversal (-ret_4w)
low vol (-vol_4w)
-volume
low amplitude (-amplitude)
```

其中 `-volume` 的 IC 最强：

```text
Val IC_mean +0.083
Test IC_mean +0.047
```

但注意：`-volume` 不能直接等同于 small-size premium。更严谨地说，它可能是：

```text
低成交活跃度
低关注度
低流动性
低拥挤度
```

不一定是真正的市值因子。

---

# 2. 当前最重要的判断

现在不要再把重点放在：

```text
继续加特征
继续跑 50 / 100 轮 GP
继续调进化参数
继续提高 IC_IR 阈值后直接重跑
```

因为目前还没有搞清楚亏损来源。

现在真正要回答的是：

```text
到底是因子本身没用？
还是成本吃掉了？
还是 short leg 拖累？
还是 long-short 结构不适合当前 A 股行情？
还是 universe 选错了？
还是周频调仓频率不合适？
还是收益 / 日期 / benchmark 对齐仍有隐藏 bug？
```

在这些问题没回答前，继续新增 EMA、MACD、北向资金、行业中性化、GP 操作符，都会把问题搞得更复杂。

---

# 3. 这次任务的核心目标

请基于当前 commit / 当前项目状态，做一次 **失败来源拆解实验**。

本次不是正式策略开发，不是最终优化。

本次目标是输出一个新的诊断报告：

```text
report/diagnosis_followup.md
```

并配套输出必要的中间表，帮助判断后续方向。

---

# 4. 严格禁止事项

本次任务请不要做以下事情：

```text
不要继续跑新的 50 轮 / 100 轮 GP 进化
不要直接把 A/B/C/D 全部实现
不要新增一堆复杂技术指标后直接重跑
不要为了收益好看修改回测口径
不要把 long-short 结果写成 A 股普通账户实盘收益
不要用 test 集挑选最优参数
不要把诊断结论直接包装成最终策略结论
不要覆盖旧 report，除非先备份或写到新文件
```

本次只做：

```text
拆解
对照
归因
小规模验证
形成 follow-up 诊断报告
```

---

# 5. 第一部分：拆解当前组合为什么亏

请先基于当前已有策略结果，拆出以下数据。

## 5.1 long leg / short leg / spread 拆解

当前策略是 long-short。

请分别输出：

```text
long_leg_return
short_leg_return
long_short_spread
strategy_gross_return
strategy_net_return
```

需要至少包含：

```text
weekly return
cumulative return
annualized return
sharpe
max_drawdown
win_rate
```

目的：判断当前负收益到底来自哪里：

```text
long leg 本身就差？
short leg 拖累？
spread 没有区分度？
成本把 gross 吃掉？
```

## 5.2 gross / net / zero-cost / with-cost 拆解

请输出：

```text
gross_return_without_cost
net_return_with_cost
cost_per_week
cumulative_cost
turnover_per_week
```

并统计：

```text
平均周换手率
中位数周换手率
90 分位周换手率
年化成本估计
成本前 Sharpe
成本后 Sharpe
```

目的：判断是不是：

```text
信号有一点点 gross alpha
但被 turnover 和成本吃掉
```

## 5.3 每周持仓状态

输出每周：

```text
date
long_count
short_count
long_avg_score
short_avg_score
long_avg_next_ret
short_avg_next_ret
turnover
gross_ret
net_ret
benchmark_ret
```

保存为：

```text
report/diagnosis_weekly_decomposition.csv
```

或者如果数据较大，用：

```text
report/diagnosis_weekly_decomposition.parquet
```

## 5.4 benchmark 对齐确认

请明确检查：

```text
策略收益日期
benchmark 收益日期
是否同一周
是否真实交易日
是否存在手动 shift / 移一天
```

至少输出一个对齐样表：

```text
date
strategy_ret
hs300_ret
zz500_ret
zz1000_ret
cyb_ret
universe_equal_weight_ret
```

注意：必须增加一个非常重要的 benchmark：

```text
universe_equal_weight_ret
```

也就是当前 universe 内股票等权收益。  
因为如果策略只是跑输 universe 等权，那说明不是大盘问题，而是排序或组合问题。

---

# 6. 第二部分：不要先 GP，先做单因子实验

报告里已经列出几个手工 IC 为正的简单因子：

```text
-ret_1w
-ret_4w
-vol_4w
-volume
-amplitude
```

请先不要继续 GP。请对这些简单因子分别做单因子测试。

## 6.1 每个单因子都要输出

对每个因子，在 train / val / test 三段分别输出：

```text
IC_mean
IC_std
IC_IR
RankIC_mean
RankIC_IR
分层收益 Q1-Q5
Top-bottom spread
long-only Top50
long-only Top100
long-short
turnover
gross_return
net_return
max_drawdown
sharpe
```

保存为：

```text
report/single_factor_diagnosis.csv
```

或：

```text
report/single_factor_diagnosis.parquet
```

## 6.2 必须同时做 long-only 和 long-short

每个单因子至少做三种组合：

```text
long_only_top50
long_only_top100
long_short_top_bottom_20pct
```

原因：当前项目已经证明 long-short 不好，但这不代表 long-only 没机会。尤其在测试期强 beta 行情中，short leg 可能是主要亏损来源。

## 6.3 单因子实验的判断标准

请在报告里回答：

```text
有没有任何单因子的 long leg 是正的？
有没有任何单因子的 long-only 跑赢 universe 等权？
有没有任何单因子只是 gross 有效、net 无效？
有没有因子在 val 有效但 test 失效？
有没有因子在 test 有效但 val 不明显，疑似偶然？
```

如果单因子都无效，后续 GP 意义很小。  
如果单因子 long-only 有效，但 long-short 亏，则说明组合结构问题更大。

---

# 7. 第三部分：universe 对照实验

当前报告说：

```text
top 400 by train-period volume 可能 anti-alpha
```

这个判断有启发，但不要直接相信，需要做对照实验。

## 7.1 Universe 版本

```text
U1_current_top400_volume
    当前逻辑，作为旧基准。

U2_amount_middle_60pct
    按 train 期 amount / 成交额 排名，剔除最高 20% 和最低 20%。

U3_total_mv_middle_60pct
    按 train 期 total_mv 排名，剔除最大 20% 和最小 20%。

U4_circ_mv_middle_60pct
    按 train 期 circ_mv 排名，剔除最大 20% 和最小 20%。

U5_liquidity_filtered_all_market
    剔除 ST、上市不足 250 日、极低成交额、极低价格后的全市场。
```

如果当前数据库暂时没有 `total_mv` / `circ_mv`，请不要硬编假数据。先在报告里说明缺字段，然后优先使用已有字段做可行版本，例如：

```text
amount
turnover_rate
volume
listed_days
is_ST
```

## 7.2 每套 universe 跑相同单因子

对每套 universe，跑同一批简单因子：

```text
-ret_1w
-ret_4w
-vol_4w
-volume
-amplitude
```

输出：

```text
universe
factor
train_IC
val_IC
test_IC
long_only_top50_net
long_only_top100_net
long_short_net
turnover
max_drawdown
sharpe
universe_equal_weight_return
excess_vs_universe_equal_weight
```

保存为：

```text
report/universe_factor_comparison.csv
```

或：

```text
report/universe_factor_comparison.parquet
```

## 7.3 这一部分要回答的问题

请在 `diagnosis_followup.md` 里明确回答：

```text
当前 top400 volume 是否真的 anti-alpha？
中等成交额 universe 是否更好？
中等市值 universe 是否更好？
-volume 因子到底更像 size、liquidity，还是 attention/crowding？
策略收益是否只是 universe beta？
```

---

# 8. 第四部分：IC_IR 阈值不要一刀切

原报告建议：

```text
IC_IR > 0.3
```

方向可以理解，但不要直接一刀切。

请做一个小网格：

```text
IC_IR >= 0.05
IC_IR >= 0.10
IC_IR >= 0.20
IC_IR >= 0.30
IC_IR >= 0.50
```

同时控制因子数量：

```text
top 3
top 5
top 10
top 20
```

输出：

```text
threshold
max_factor_count
selected_factor_count
gross_return
net_return
turnover
sharpe
max_drawdown
```

保存为：

```text
report/icir_threshold_grid.csv
```

这一部分只做轻量测试，不要扩大成新的大规模 GP 搜索。

---

# 9. 第五部分：生成 diagnosis_followup.md

最后请生成：

```text
report/diagnosis_followup.md
```

报告结构如下：

```markdown
# claudets follow-up diagnosis: where negative alpha comes from

## 1. Background

说明前一份 diagnosis_report.md 的结论：
- 工程硬伤大多已修
- 50 轮 clean run 仍全负
- 简单因子 IC 方向存在但很弱
- 当前不能继续盲目 GP

## 2. Current Strategy Decomposition

展示：
- long leg
- short leg
- long-short spread
- gross vs net
- turnover
- cost impact
- benchmark alignment

明确回答：
- 是 long leg 没用？
- 是 short leg 拖累？
- 是成本吃掉？
- 是 spread 没有区分度？

## 3. Single Factor Diagnosis

展示每个简单因子：
- IC
- long-only
- long-short
- turnover
- gross/net
- 是否跑赢 universe equal weight

明确回答：
- 有没有单因子值得继续研究？
- 哪些因子只是 IC 好看但组合不赚钱？

## 4. Universe Comparison

展示不同 universe 下的表现。

明确回答：
- top400 volume 是否 anti-alpha？
- middle 60% 是否改善？
- -volume 到底像什么因子？

## 5. IC_IR Threshold Grid

展示阈值和因子数量变化对结果的影响。

明确回答：
- 提高 IC_IR 是否真的改善？
- 是不是因子越少越好？

## 6. Final Diagnosis

请根据实验结果选择以下结论之一或多个：

- 因子本身无效
- long-short 结构不适合当前行情
- short leg 是主要亏损来源
- 成本是主要亏损来源
- universe 选择是主要问题
- 周频调仓频率不合适
- 仍可能存在隐藏数据 / 对齐 bug

## 7. Recommended Next Step

根据结果选择下一步：

- 如果 long leg 有效：优先开发 long-only
- 如果 zero-cost 有效、net 无效：优先降频 / 降换手 / 成本模型
- 如果 universe 改善明显：优先重构 universe
- 如果单因子都无效：停止 GP，重构研究方向
- 如果只有 test 好、val 不好：视为不稳定，不要采用
```

---

# 10. 验收标准

本次任务完成后，至少应有以下文件：

```text
report/diagnosis_followup.md

report/diagnosis_weekly_decomposition.csv 或 .parquet
report/single_factor_diagnosis.csv 或 .parquet
report/universe_factor_comparison.csv 或 .parquet
report/icir_threshold_grid.csv 或 .parquet
```

如果某些文件因为当前代码结构暂时不能直接生成，请说明原因，并至少生成：

```text
report/diagnosis_followup_plan.md
```

里面列出需要新增哪些函数 / 类 / 脚本。

---

# 11. 建议新增脚本

建议不要把所有逻辑塞进原来的 `autonomous_loop.py`。

可以新增一个诊断脚本，例如：

```text
diagnostics/followup_diagnosis.py
```

或者：

```text
scripts/run_followup_diagnosis.py
```

它只负责读当前已有数据和模型结果，生成诊断表。

推荐结构：

```python
def load_current_results():
    ...

def decompose_current_strategy():
    ...

def run_single_factor_tests():
    ...

def build_universe_variants():
    ...

def run_universe_comparison():
    ...

def run_icir_threshold_grid():
    ...

def generate_followup_report():
    ...

def main():
    ...
```

---

# 12. 本次任务结束时必须汇报

请在任务结束时输出：

```text
1. 本次读了哪些文件
2. 本次新增 / 修改了哪些文件
3. 是否运行 python -m compileall -q .
4. 是否实际跑了诊断实验
5. 生成了哪些 report 文件
6. 当前最可能的失败来源是什么
7. 下一步建议是什么
```

---

# 13. 最重要的提醒

现在不要再继续“炼丹式 GP”。

先把失败拆开：

```text
long leg
short leg
成本
换手
universe
单因子
benchmark
```

拆清楚以后，再决定是：

```text
做 long-only
改 universe
降频
加特征
做行业中性化
还是停止这条路线
```

否则继续加功能，只会让项目越来越复杂，但不知道到底为什么亏。
