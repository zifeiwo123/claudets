# AGENTS.md — claudets 工程治理版

本文件只服务于当前项目：`claudets`。

这个项目不是普通 Python 小脚本，而是一个 **A 股自动因子研究 / 周频回测 / 报告生成工程**。  
Codex 在本项目中工作时，目标不是“把收益调好看”，而是维护一个可复现、可解释、可扩展的研究工程。

---

## 0. 当前项目定位

`claudets` 的合理定位：

```text
A 股周频自动 Alpha 因子研究平台
```

核心职责：

```text
数据接入 / 数据清洗
→ 周频聚合 / 样本切分
→ 因子表达式生成
→ 因子计算
→ IC / 分层 / 稳定性评价
→ long-short / long-only 组合回测
→ 报告生成与实验留痕
```

Codex 的首要职责：

```text
维护工程结构
维护研究口径
维护代码质量
维护报告真实性
```

不要把本项目直接包装成“已经可实盘的策略系统”。

---

## 1. 全局工作原则

### 1.1 先理解，再修改

每次涉及代码修改前，必须先快速回答：

```text
1. 这次任务属于哪个模块？
2. 会影响哪些数据口径？
3. 会影响哪些回测指标？
4. 会影响哪些 report 输出？
5. 是否需要重新跑实验？
```

除非用户明确要求“直接小改”，否则不要跳过这个判断。

---

### 1.2 研究代码不能靠“跑赢结果”反推正确

在这个项目里，以下行为禁止：

```text
为了提高收益而修改回测口径
为了降低回撤而事后裁剪收益序列
为了让报告好看而只展示最优 iteration
把 long-short 结果写成 A 股普通账户实盘结果
把未验证的数字写成策略结论
```

如果收益变低但口径更可信，优先接受可信口径。

---

### 1.3 源数据只读，结果另存

默认原则：

```text
源数据表 / 原始数据库：只读
实验结果 / 报告 / 中间表：写入独立输出目录或结果库
```

特别注意：

```text
daily_qfq / daily / adj_factor / tushare_local.db 等源数据，不要随意覆盖
大结果优先 parquet / sqlite / duckdb，不要默认大量 CSV
```

---

### 1.4 每次改完都要有“完成定义”

每轮任务结束前必须说明：

```text
修改了哪些文件
为什么这样改
有没有跑语法检查 / 单元检查
是否需要重跑回测
哪些结论仍不能使用
下一步建议
```

不要只说“已优化”。

---

## 2. 推荐工程目录职责

如果当前项目目录和下面不完全一致，以实际代码为准，但职责边界应尽量保持。

```text
config/
    参数、路径、token 环境变量读取、全局常量。
    禁止明文 token、密钥、账号。

data/
    数据下载、数据加载、日频清洗、周频聚合、样本切分。
    重点维护复权、日期、收益对齐、股票池口径。

factors/
    表达式树、因子生成、因子池、因子计算。
    重点维护 factor_id、表达式可复现、方向、去重。

evaluation/
    IC、RankIC、分层、稳定性、样本外验证。
    重点维护 train/valid/test 口径。

portfolio/
    权重、组合构建、交易成本、滑点、回撤控制。
    重点维护 long-short 与 long-only 区分、换手率成本、风控时点。

pipeline/
    端到端流程编排、报告生成、实验记录。
    重点维护入口一致性、流程可重复、输出留痕。

report/
    生成报告、summary、图表、CSV/parquet 中间结果。
    报告只反映已实现、已验证的内容。
```

---

## 3. 数据口径规范

### 3.1 A 股价格优先前复权

A 股研究中，默认优先使用前复权行情。

如果使用本地 SQLite：

```text
daily_qfq.qfq_open       -> open
daily_qfq.qfq_high       -> high
daily_qfq.qfq_low        -> low
daily_qfq.qfq_close      -> close
daily_qfq.qfq_pre_close  -> pre_close
```

如果使用在线 Tushare，应明确是否使用：

```text
pro_bar(adj="qfq")
```

报告中必须写清楚：

```text
是否前复权
数据源
数据区间
股票池构造方式
```

---

### 3.2 周频日期用真实交易日

周频聚合应使用该周最后一个真实交易日作为 `trade_date`。

不要让策略交易日期落在周六 / 周日。

---

### 3.3 因子与收益必须有明确时点

默认研究范式：

```text
t 周因子
→ t+1 周持有收益
```

如果采用其他方式，必须在代码和报告中写清楚。

---

### 3.4 股票池不能偷看未来

构造 universe 时，禁止用验证期 / 测试期全段信息筛股票。

优先做法：

```text
用 train 期确定固定 universe
valid/test 沿用
```

更高级做法：

```text
滚动 universe，但每期只使用 t-1 之前的信息
```

---

## 4. 回测口径规范

### 4.1 long-short 与 long-only 必须分开

如果组合逻辑是：

```text
做多高分组
做空低分组
```

报告中必须称为：

```text
long-short 因子研究组合
```

不能称为 A 股普通账户实盘收益。

如果要贴近用户交易，必须有：

```text
long-only TopN
long-only Top百分比
或者候选池评分
```

---

### 4.2 成本按换手率扣，不按收益乘法扣

禁止：

```python
net_ret = raw_ret * (1 - cost)
```

推荐：

```python
turnover = 0.5 * sum(abs(weight_t - weight_t_minus_1))
net_ret = raw_ret - turnover * cost_rate
```

如果暂时简化，也必须明确是近似成本。

---

### 4.3 风控只能用历史信息

禁止：

```python
returns.clip(lower=-0.03)
```

这种属于事后修改历史收益。

风控信号必须只使用当期之前可见数据，例如：

```python
rolling_vol = returns.shift(1).rolling(12).std()
```

---

## 5. 因子研究规范

### 5.1 因子表达式必须可复现

报告中不应只显示：

```text
ts_mean(close)
```

而应显示：

```text
ts_mean(close, 20)
```

表达式必须包含：

```text
字段名
操作符
窗口参数
左右子树
```

---

### 5.2 负 IC 因子要记录方向

如果验证集 IC 为负，说明因子高值对应未来低收益。  
应明确记录：

```text
raw_ic
direction
adjusted_ic
```

组合排序使用方向调整后的因子值。

---

### 5.3 不要迷信单次最优 iteration

多轮自动搜索应报告整体分布：

```text
均值
中位数
最大 / 最小
胜率
回撤分布
不同 benchmark 下表现
```

不要只展示最优轮次。

---

## 6. 报告规范

主报告必须分清：

```text
已实现
部分实现
未实现
实验结果
风险与局限
下一步计划
```

报告数字必须来自统一结果源，例如：

```text
summary.json
summary.parquet
backtest_result.parquet
```

同一个指标不要在多个脚本里重复计算导致口径不一致。

---

## 7. agent 使用策略

本项目默认使用这些项目级 subagent：

```text
project-architect
data-contract-steward
research-methodology-reviewer
backtest-governance-reviewer
implementation-quality-reviewer
report-governance-reviewer
release-handoff-manager
```

推荐触发方式：

```text
方案 / 结构 / 模块边界：project-architect
数据 / 表结构 / 复权 / 日期：data-contract-steward
因子 / 假设 / 过拟合：research-methodology-reviewer
回测 / 成本 / 股票池 / 风控：backtest-governance-reviewer
代码 / 接口 / 可运行性：implementation-quality-reviewer
报告 / summary / 结论：report-governance-reviewer
交付 / 版本 / 下一步：release-handoff-manager
```

当用户说“全局审查”“从工程角度设计”“整理方案”时，优先让 `project-architect` 统筹，再让其他 agent 分工。

---

## 8. hooks 作用

本项目启用 hooks 后，Codex 会在关键节点自动做工程守门：

```text
UserPromptSubmit：每次用户发话后注入项目规则
PreToolUse：执行 Bash/Edit/Write 前检查风险
PostToolUse：修改后自动做静态检查和 compileall
Stop：改过文件后，停止前要求补交付摘要
```

hooks 不能代替研究判断，但可以减少明显工程事故。

---

## 9. 常用命令

进入 Codex 后可用：

```text
/project-audit      全局工程审查
/preflight          执行前计划
/postcheck          执行后检查
/report-review      报告一致性检查
/handoff            生成交付摘要
/runbook            生成运行手册
```

---

## 10. 最重要的一句话

这个项目的目标是：

```text
把量化研究流程做可信
而不是把某一次回测收益做漂亮
```
