$null = [Console]::In.ReadToEnd()

@"
[claudets project rules]
This is an A-share weekly alpha research, backtest, and reporting project.
Before code/report edits, check module scope, data specification impact, backtest metric impact, report impact, and whether experiments must be rerun.
- Treat raw data/db/parquet files as read-only unless the user explicitly approves.
- Do not hard-code tokens or API keys; use environment variables.
- Prefer qfq prices; if not available, reports must say the results are engineering-only.
- Use real weekly trading dates and t factor -> t+1 forward returns.
- Weekly rebalancing should preferably be guided by daily-derived features sampled at the week-end snapshot.
- Use train-period universe for valid/test unless a no-lookahead rolling universe is implemented.
- Store validation IC/direction for factor selection and signal flipping; do not use train IC for test decisions.
- Deduct cost as raw_ret - turnover * cost_rate; do not multiply returns by (1-cost).
- Do not clip historical returns for drawdown control.
- Separate long-short research portfolios from long-only trade-like portfolios.
- After edits, report changed files, checks run, rerun needs, invalid old conclusions, and next steps.
"@

exit 0
