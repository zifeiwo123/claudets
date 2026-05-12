请对刚才的修改做 postcheck。

必须检查：

1. 列出本轮修改文件。
2. 尽量运行语法检查：
   - 若 `python` 可用：`python -m compileall -q .`
   - 若只有 `py` 可用：`py -3 -m compileall -q .`
   - 若都不可用，明确说明未能运行。
3. 检查是否引入：
   - 明文 token/key/secret
   - 源数据或行情 parquet 直接覆盖
   - 用训练集 IC 决定测试组合方向
   - `ret * (1-cost)` 或类似乘法扣成本
   - 事后 `clip(lower=...)` 裁剪组合收益
   - 周频日期使用 `dt.start_time`
   - long-short 和 long-only 报告混淆
4. 检查“日线特征指导、周频调仓”是否仍成立：日线特征只能在周末快照取值，收益仍是下一周持有收益。
5. 判断是否需要重新跑回测或重新生成 report。
6. 输出剩余风险和下一步。
