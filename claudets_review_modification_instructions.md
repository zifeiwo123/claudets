# claudets 项目审查与修改建议

> 用途：本文档用于交给 Claude / 其他代码助手继续修改项目。  
> 审查目标：  
> 1. 检查方案有无硬伤  
> 2. 检查程序文件有无硬伤  
> 3. 检查各个 report.md / report_v*.md，并给出修改建议与思考  

---

## 一、总体结论

当前项目方向是对的：

```text
自动因子生成 → 训练/验证/测试 → 组合构建 → 回测 → 报告生成
```

这条链路值得保留。

但是当前版本**不能作为有效回测结论使用**。  
问题不只是“收益好坏”，而是存在几处会直接污染结论的硬伤：

1. 回测策略本质是 long-short，不是 A 股普通账户可直接执行的 long-only 策略。
2. 多轮迭代后挑选最佳测试结果，存在测试集调参 / 过拟合问题。
3. 负 IC 因子没有反向使用，导致信号方向可能完全反了。
4. 交易成本扣法错误，亏损时成本反而会让亏损变小。
5. 回撤控制存在事后修正，属于未来函数式处理。
6. 测试期股票池选择使用了未来成交量信息。
7. 周频日期锚点错位。
8. 数据没有前复权，A 股回测会被除权污染。
9. report.md 中有些内容把“设计目标”写成了“已实现功能”，报告结论与代码实现不完全一致。

因此，当前首要任务不是继续优化收益，而是先把**回测可信度、数据口径、报告一致性**修干净。

---

# 二、方案层硬伤

## 2.1 当前是 long-short 策略，不是 A 股实盘多头策略

### 问题

程序里的组合构造逻辑大致是：

```python
做多最高分 20%
做空最低分 20%
```

这本质上是一个 long-short 组合。

### 影响

A 股普通账户很难直接做空个股，因此这个结果不能直接代表实盘可执行的 A 股波段策略。

如果报告中直接把 long-short 收益写成“Alpha 策略收益”，容易误导结论。

### 修改建议

建议保留两套回测：

#### 1. long-short 版本

用于因子研究，观察因子是否有截面区分能力。

#### 2. long-only 版本

用于接近 A 股实盘，建议做：

```text
每周买入因子排名前 N 的股票
例如 Top 30 / Top 50 / Top 100
不做空
和沪深300、创业板、全A等权、Top400等权比较
```

报告里必须明确区分：

```text
long-short 因子研究收益
long-only 实盘近似收益
```

---

## 2.2 周频样本太短，遗传规划极易过拟合

### 问题

训练集、验证集、测试集大致是：

```text
训练集：2023-01 到 2024-06
验证集：2024-07 到 2025-06
测试集：2025-07 到 2026-05
```

周频数据下，每一段只有几十个时间点。

同时项目又自动生成大量因子，并通过多轮进化、筛选、组合来寻找结果。

### 影响

这种设定非常容易出现：

```text
不是找到了真实有效因子
而是随机搜索碰巧撞中了某一段行情
```

尤其 `autonomous_loop.py` 连续运行 20 轮，然后报告中突出第 18 轮的高收益 / 高 Sharpe，本质上容易变成：

```text
用测试集选模型
```

这会导致测试集不再是严格意义上的测试集。

### 修改建议

1. 训练集和验证集用于生成因子、筛选因子、调参。
2. 测试集只能最后看一次，不能用测试集选择第几轮最好。
3. 如果要跑 20 轮，需要在训练 + 验证中选出最佳轮次，然后再统一评估测试集。
4. 更好方式是增加 final holdout：

```text
train: 2023-01 ~ 2024-06
valid: 2024-07 ~ 2025-06
test:  2025-07 ~ 2025-12
final_holdout: 2026-01 ~ 2026-05
```

5. 报告中不要只展示最佳 iteration，要展示所有 iteration 的分布。

---

## 2.3 因子大量使用原始价格 / 成交量，不是稳定 alpha

### 问题

报告和程序里大量出现以下原始字段：

```text
volume
open
high
low
close
ts_mean(volume)
ts_rank(high)
scale(open)
```

这些直接使用原始价格和成交量的因子，容易混入：

```text
价格水平
市值暴露
流动性暴露
成交活跃度暴露
```

它们不一定是真正稳定的 alpha。

### 影响

例如：

```text
volume 越大
```

可能只是大市值股票、热门股、流动性好的股票，而不是一个可以独立解释未来收益的信号。

### 修改建议

优先改造成更合理的基础特征：

```text
ret_1w：1周收益率
ret_4w：4周收益率
ret_12w：12周收益率
vol_ratio_4_20：近4周成交量 / 近20周成交量
turnover_ratio：换手率
hl_range_pct = (high - low) / close
close_position = (close - low) / (high - low)
ma_distance：价格相对均线距离
atr_pct：ATR / close
drawdown_20：20日或20周回撤
```

后续再让遗传规划在这些相对化、标准化后的特征上生成表达式。

---

# 三、程序文件硬伤

## 3.1 Tushare token 明文写在文件里

### 问题

`plan.md` 和 `config/settings.py` 中存在 Tushare token 明文。

### 影响

1. 如果上传 GitHub 或发给他人，会泄露 token。
2. 如果 token 是真实有效的，存在被滥用风险。

### 修改建议

删除所有硬编码 token，改用环境变量：

```python
import os

TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")

if not TUSHARE_TOKEN:
    raise ValueError("请先设置环境变量 TUSHARE_TOKEN")
```

如果 token 已经泄露，建议去 Tushare 后台重置。

---

## 3.2 主入口 main.py / pipeline.workflow.py 有运行硬伤

### 问题

`pipeline/workflow.py` 中类似：

```python
engine = EvolutionEngine(FactorCompute(self.data["train"]))
...
result = engine.run(self.data["train"], self.data["val"])
```

但 `EvolutionEngine` 的构造函数大致是：

```python
EvolutionEngine(train_data, val_data)
```

而且 `engine.run()` 不接收参数。

### 影响

主 pipeline 即使依赖安装完整，也会在 step5 附近崩溃。

目前真正能跑的更像是：

```text
run_iteration.py
autonomous_loop.py
```

但主入口不可靠。

### 修改建议

统一 `EvolutionEngine` 的接口。

建议改成其中一种风格：

#### 方案 A：构造函数传数据，run 不传数据

```python
engine = EvolutionEngine(train_data, val_data)
result = engine.run()
```

#### 方案 B：构造函数不传数据，run 传数据

```python
engine = EvolutionEngine()
result = engine.run(train_data, val_data)
```

整个项目只保留一种风格，避免入口不一致。

---

## 3.3 因子池去重和 ID 管理有严重 bug

### 问题 1：factor_id 重复

`FactorGenerator.generate_pool()` 每一批都会生成：

```text
alpha_000
alpha_001
alpha_002
...
```

但是 `autonomous_loop.py` 中多批生成：

```python
for batch in range(4):
    all_factors.extend(generator.generate_pool(8))
```

每批都从 `alpha_000` 开始，导致 factor_id 重复。

### 影响

`FactorPool.add()` 没有正确处理同名 factor_id，会覆盖旧因子，还可能留下旧 hash。

结果是：

```text
以为生成了 20~30 个因子
实际有效进入池里的可能只有 8 个左右
```

`report/factor_evals.csv` 中只有 8 行，说明这个问题已经实际发生。

### 修改建议

factor_id 必须全局唯一。

可以使用：

```python
factor_id = f"alpha_{global_counter:05d}"
```

或者：

```python
import uuid
factor_id = f"alpha_{uuid.uuid4().hex[:8]}"
```

---

### 问题 2：structure_hash 对叶子节点过度简化

当前 `ExprNode.structure_hash()` 对叶子节点只返回：

```python
"LEAF"
```

不区分：

```text
open
high
low
close
volume
窗口参数
```

### 影响

如下两个表达式可能被当成同一种结构：

```text
ts_mean(open, 5)
ts_mean(close, 60)
```

这会误删大量本该保留的因子。

### 修改建议

改为：

```python
def structure_hash(self) -> str:
    if self.is_leaf:
        return f"LEAF:{self.op}:{self.param}"

    left_h = self.left.structure_hash() if self.left else ""
    right_h = self.right.structure_hash() if self.right else ""

    return hashlib.md5(
        f"{self.op}|{self.param}|{left_h}|{right_h}".encode()
    ).hexdigest()[:12]
```

同时要确保表达式中的窗口参数也进入 hash。

---

## 3.4 负 IC 因子没有反向使用，这是核心硬伤

### 问题

报告里很多 Top 因子都是负 IC，例如：

```text
Train IC < 0
Val IC < 0
```

负 IC 的含义是：

```text
因子值越高，未来收益越低
```

正确做法应该是把这个因子乘以 -1，再用于排序。

但当前组合里直接把高分 20% 做多、低分 20% 做空，没有根据验证集 IC 方向翻转信号。

`icir_weight()` 里也使用了 `abs(ic_ir)`，但是没有保留方向。

### 影响

这会导致一个很严重的问题：

```text
系统明明识别出“高值未来更差”的因子
却仍然可能拿高值去做多
```

最终组合方向可能完全反了。

### 修改建议

每个因子都需要记录方向：

```python
direction = 1 if val_ic_mean > 0 else -1
signal = raw_factor * direction
```

或者在权重中保留符号：

```python
weight = ic_ir
```

不要只使用：

```python
abs(ic_ir)
```

组合、分层测试、报告展示都要统一使用调整方向后的因子值。

报告中也应显示：

```text
原始 IC
使用方向
调整后 IC
```

---

## 3.5 交易成本扣法错误

### 问题

当前交易成本类似这样处理：

```python
rets_net = rets_raw * (1 - SLIPPAGE_RATE * 2)
```

### 影响

这种写法不对。

如果某周收益是 -5%，乘以 0.996 后变成 -4.98%，亏损反而减少了。

交易成本不应该让亏损减少。

### 修改建议

应基于换手率扣成本：

```python
rets_net = rets_raw - turnover * cost_rate
```

需要保存每周持仓，计算换手率：

```python
turnover_t = 0.5 * sum(abs(weight_t - weight_t_minus_1))
```

大致逻辑：

```python
gross_ret_t = sum(weight_{t-1} * stock_ret_t)
cost_t = turnover_t * cost_rate
net_ret_t = gross_ret_t - cost_t
```

如果暂时无法实现完整换手率，至少先用固定惩罚：

```python
rets_net = rets_raw - fixed_cost_per_rebalance
```

但不能用乘法扣成本。

---

## 3.6 回撤控制存在未来函数 / 事后修正

### 问题

`autonomous_loop.py` 中类似：

```python
if final_dd < -0.15:
    rets_final = rets_final.clip(lower=-0.03)
```

这等于：

```text
回测结束后发现回撤太大
于是把历史上所有单周亏损强行截断到 -3%
```

### 影响

这不是真实风控，而是事后改成绩。

真实交易中不能在亏损发生后回头修改亏损。

### 修改建议

删除这种事后 clip。

如果要做风控，只能使用当期之前已知的信息，例如：

```python
rolling_vol = rets_net.shift(1).rolling(12).std()
hist_vol = rolling_vol.shift(1).rolling(52).mean()
```

然后根据前一周已经知道的波动率决定下一周仓位。

正确结构：

```python
risk_signal_t = function(data up to t-1)
position_t = adjust_position(risk_signal_t)
return_t = position_t * raw_return_t
```

不能使用当期或未来收益来决定当期风控。

---

## 3.7 股票池选择存在未来信息

### 问题

`FactorCompute` 初始化时使用当前数据段的平均成交量选 Top N：

```python
vol_mean = self.raw.groupby("ts_code")[vol_col].mean()
```

如果在测试集里执行这个逻辑，相当于用整个测试期的未来成交量来确定测试期股票池。

### 影响

这属于未来信息泄漏。

例如某只股票在测试期后半段大涨、成交量暴增，它可能因为未来成交量高而被纳入测试股票池。

### 修改建议

可选方案：

#### 方案 A：固定股票池

用训练期末或训练期整体的成交额 Top N 确定股票池，验证集和测试集都沿用。

```text
train period 选出 Top400
valid/test 都只在这 Top400 中回测
```

#### 方案 B：滚动股票池

每周只使用该周之前的数据选股票池：

```text
在 t 周回测时
只能使用 t-1 周及以前的成交量 / 成交额
```

初期建议先用方案 A，简单稳定。

---

## 3.8 周频日期锚点错误

### 问题

`Preprocessor.to_weekly()` 中类似：

```python
weekly["week"] = weekly["week"].dt.start_time
```

如果使用 `W-FRI`，`start_time` 可能是周六，不是真实交易周五。

### 影响

报告中可能出现策略日期落在周六，后续再手动往前移一天对齐基准。

这会造成日期口径混乱。

### 修改建议

周频数据应该使用该周最后一个真实交易日作为 `trade_date`。

建议在 groupby 周期时保留：

```python
last_trade_date = group["trade_date"].max()
```

最终周频表用真实交易日，而不是 period 的 start_time。

---

## 3.9 数据没有前复权，A 股多年回测会被除权污染

### 问题

当前下载的是 Tushare `daily` 原始行情，不是前复权行情。

### 影响

A 股存在分红、送转、除权。  
如果使用未复权价格计算收益率、均线、突破、回撤，会污染结果。

### 修改建议

使用前复权数据：

#### 方案 A：Tushare pro_bar

```python
pro_bar(ts_code=code, adj="qfq")
```

#### 方案 B：使用本地库 daily_qfq

用户原本的研究习惯是优先使用本地 SQLite 中的 `daily_qfq` 表。

建议后续直接兼容：

```text
C:\Users\liuji\Desktop\tslearn\01_tsdb\tushare_local.db
或当前项目指定的本地 tushare_local.db
```

并注意字段映射：

```text
qfq_open  -> open
qfq_high  -> high
qfq_low   -> low
qfq_close -> close
qfq_pre_close -> pre_close
```

---

# 四、report.md / report_v*.md 的问题

## 4.1 report.md 中有些内容和实际程序不一致

### 问题

`report/report.md` 中写到了：

```text
结构哈希 + Spearman 相关性双重去重
三阶段回撤改进循环
按市值五档滑点
风险平价 / MaxDD 最小化
```

但实际程序中：

1. 相关性去重基本没有真正参与主流程。
2. 回撤控制中的风险平价阶段更像空壳。
3. 滑点没有真正按市值分档，只用了默认固定滑点。
4. 极值损失截断是事后 clip，不是可交易风控。

### 影响

报告把“设计目标”写成了“已实现功能”，会造成误导。

### 修改建议

报告必须拆成：

```text
已实现
部分实现
未实现 / 待实现
```

例如：

```markdown
## 已实现
- 自动生成表达式因子
- 训练 / 验证 / 测试切分
- 基础 IC 评价
- 基础多空组合回测

## 部分实现
- 回撤控制：已有初步框架，但当前 clip 方法不可用于正式回测
- 成本扣除：已有参数，但当前扣法需要修正为换手率成本

## 未实现 / 待实现
- 行业 / 市值中性化
- Spearman 相关性去重
- 市值分档滑点
- long-only 实盘近似回测
- final holdout 验证
```

---

## 4.2 各个 report_v 的结论不稳定

### 问题

20 个 iteration 中结果差异极大，例如：

```text
最好：+60.8%，Sharpe 3.94
较差：-37.2%，Sharpe -3.96
```

### 影响

这说明策略没有稳定性。  
更像随机搜索在测试集上撞结果，而不是稳定可复用策略。

### 修改建议

报告不能只突出最好的 iteration。

应该增加总体分布表：

```text
收益均值
收益中位数
收益最大值
收益最小值
Sharpe 均值
Sharpe 中位数
跑赢沪深300的比例
跑赢创业板的比例
MaxDD 超过 15% 的比例
```

建议新增：

```text
report/iteration_summary.md
report/iteration_summary.csv
```

---

## 4.3 benchmark 对齐和报告数值不一致

### 问题

不同报告中的 benchmark 数值不完全一致。

例如：

```text
report.md：策略 +20.2%，沪深300 +15.8%
report_v20.md：策略 +20.4%，沪深300 +17.6%
summary.json：策略 +20.35%，沪深300 +17.55%
```

### 影响

说明报告生成链路不是同一套口径。

### 修改建议

统一所有报告都从同一个结果源读取：

```text
summary.json
summary.csv
backtest_result.parquet
```

不要多个脚本各自重新计算 benchmark。

建议封装统一函数：

```python
load_backtest_summary()
load_benchmark_returns()
align_strategy_and_benchmark()
```

所有报告只能调用这一套函数。

---

## 4.4 因子表达式没有显示参数，无法复现

### 问题

报告中出现：

```text
ts_mean(close)
ts_rank(high)
delta(volume)
```

但没有窗口参数。

无法知道：

```text
ts_mean(close) 是 5 周、20 周还是 60 周
delta(volume) 是 1 周差分还是 5 周差分
```

### 影响

报告不可复现。

### 修改建议

修改表达式的 `__repr__` 或展示函数，让它显示参数：

```text
ts_mean(close, 20)
ts_rank(high, 10)
delta(volume, 3)
```

如果是二元表达式，也要完整展示：

```text
div(ts_mean(close, 20), ts_mean(close, 60))
sub(rank(volume), rank(close))
```

---

## 4.5 报告格式问题

### 问题

负收益可能显示为：

```text
+-37.2%
+-15.4%
```

### 修改建议

格式化函数改成：

```python
def fmt_pct(x):
    return f"{x:.1%}"
```

不要手动拼接 `"+"`。

如果一定要显示正号：

```python
def fmt_pct_signed(x):
    return f"{x:+.1%}"
```

这样负数会自然显示为：

```text
-37.2%
```

正数显示为：

```text
+20.4%
```

---

# 五、建议修改优先级

## 5.1 第一优先级：先让回测可信

这些是必须优先修的硬伤：

1. 删除 Tushare token，改成环境变量读取。
2. 修复主入口 `main.py` / `pipeline.workflow.py` 的接口不一致问题。
3. 修复 `FactorPool.structure_hash()`。
4. 修复 factor_id 重复问题。
5. 修复负 IC 因子方向，验证集 IC < 0 的因子必须反向。
6. 修复交易成本，必须用换手率扣成本。
7. 删除 `clip(lower=-0.03)` 这种事后回撤修正。
8. 固定股票池，禁止用测试期平均成交量选股。
9. 改成前复权数据。
10. 修复周频日期锚点，用真实交易周最后一个交易日。

---

## 5.2 第二优先级：让报告可信

1. 每个因子表达式显示窗口参数。
2. report.md 不要把“未实现功能”写成“已实现”。
3. 20 轮报告不要挑最好，必须统计整体分布。
4. benchmark 对齐只保留一套函数。
5. 增加 long-only 回测结果。
6. 对每个报告增加“数据口径说明”：

```text
数据来源
是否前复权
调仓频率
交易成本
股票池构造方式
是否允许做空
是否使用测试集选模型
```

---

## 5.3 第三优先级：再谈进化和优化

等基础可信度修完以后，再考虑：

```text
行业中性化
市值中性化
流动性中性化
walk-forward 验证
final holdout 验证
IC decay
分市场阶段检验
TopN 多头组合
持仓换手约束
涨跌停 / 停牌处理
最大持仓数量限制
个股权重上限
```

---

# 六、建议 Claude 执行的具体任务清单

## 任务 1：安全配置修复

- 删除所有明文 Tushare token。
- 在 `config/settings.py` 中改为读取环境变量。
- 更新 README，说明如何设置：

```powershell
setx TUSHARE_TOKEN "你的token"
```

或者临时设置：

```powershell
$env:TUSHARE_TOKEN="你的token"
```

---

## 任务 2：修复主 pipeline 入口

检查并统一以下文件接口：

```text
main.py
pipeline/workflow.py
engine/evolution.py
run_iteration.py
autonomous_loop.py
```

目标是：

```powershell
python main.py
```

可以正常跑完整流程。

---

## 任务 3：修复因子 ID 和结构哈希

需要修改：

```text
factor_generator.py
factor_pool.py
expression_tree.py
```

要求：

1. 每个 factor_id 全局唯一。
2. structure_hash 必须包含：
   - 操作符 op
   - 字段名
   - 参数 param
   - 左右子树结构
3. 不允许把所有叶子节点都记成 `"LEAF"`。

---

## 任务 4：修复因子方向

在因子评价阶段记录：

```text
train_ic_mean
val_ic_mean
direction
adjusted_val_ic
```

规则：

```python
direction = 1 if val_ic_mean >= 0 else -1
adjusted_factor = raw_factor * direction
```

组合构建时使用 `adjusted_factor`。

报告中同时展示原始 IC 和使用方向。

---

## 任务 5：修复交易成本

删除：

```python
rets_net = rets_raw * (1 - cost)
```

改成：

```python
rets_net = rets_raw - turnover * cost_rate
```

需要保存每周持仓权重，计算换手率。

---

## 任务 6：删除事后回撤 clip

删除类似：

```python
rets_final = rets_final.clip(lower=-0.03)
```

如果需要风控，只能使用 `shift(1)` 后的历史信息。

---

## 任务 7：修复股票池未来信息

不要在测试集内部用全期平均成交量选股票池。

优先实现固定股票池：

```text
用训练期末或训练期整体 Top400 成交额股票作为 universe
valid/test 沿用同一个 universe
```

后续再做滚动股票池。

---

## 任务 8：使用前复权数据

优先支持本地 SQLite `daily_qfq` 表。

字段映射：

```text
qfq_open       -> open
qfq_high       -> high
qfq_low        -> low
qfq_close      -> close
qfq_pre_close  -> pre_close
```

如果继续使用 Tushare 在线接口，则使用 `pro_bar(adj="qfq")`。

---

## 任务 9：修复周频日期

周频聚合时使用每周最后一个真实交易日：

```python
week_trade_date = group["trade_date"].max()
```

不要使用 period 的 start_time 作为策略日期。

---

## 任务 10：重写 report.md 结构

报告应改为：

```markdown
# 自动因子生成策略报告

## 1. 数据口径
- 数据来源：
- 是否前复权：
- 回测区间：
- 调仓频率：
- 股票池构造：
- 是否允许做空：
- 交易成本：

## 2. 已实现功能

## 3. 部分实现功能

## 4. 尚未实现功能

## 5. 因子表现

## 6. long-short 回测结果

## 7. long-only 回测结果

## 8. 20轮迭代稳定性分析

## 9. 风险与局限

## 10. 下一步修改计划
```

---

# 七、最终判断

当前项目最大价值在于：

```text
已经跑通了自动因子研究的大框架
```

但当前结果不能直接当作有效策略结论。

现阶段最重要的不是继续追求更高收益，而是先修：

```text
因子方向
交易成本
股票池未来信息
回撤事后修正
前复权数据
报告一致性
```

修完以后，收益大概率会下降，但可信度会明显提高。

一个真实可信的 +5% ~ +15% 超额收益，远比当前可能带有口径问题的 +60% 高 Sharpe 更有价值。
