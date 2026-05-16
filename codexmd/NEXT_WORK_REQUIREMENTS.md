# Next Work Requirements

This file records the current planning requirements for future Codex / Claude
work on `claudets`.

Keep this document ASCII-safe. The project has had encoding drift before, so
new governance notes should avoid non-ASCII text unless explicitly required.

---

## Current Governing State

As of the latest local check:

```text
Final holdout: preliminary pass
GP: paused
Phase 2: paused
```

The lightweight monitor currently passes:

```powershell
python diagnostics\final_holdout_monitor_check.py
```

Recent observed metrics from `report/final_holdout_metrics.json`:

```text
Holdout weeks: 13
IR vs EW: +0.4132
Annualized excess return: +3.350%
Weekly excess win rate: 61.5%
Conclusion: preliminary pass
```

These numbers do NOT constitute final PASS. They only support the current
`preliminary pass` status.

---

## Immediate Rules

- Do not restart GP.
- Do not enter Phase 2.
- Do not promote the final holdout to PASS while it has only 13 weeks.
- Do not manually edit report metrics.
- Do not overwrite source data parquet/db files.
- Do not change universe, factor, TopN, cost rate, or holdout parameters just to
  improve results.
- Do not describe long-only backtest returns as a production-ready A-share
  strategy.
- Keep final holdout reports generated from a single source:
  `diagnostics/final_holdout_audit.py`.

---

## Highest Priority: Report-Generation Governance

The next engineering task should keep report-generation sources from
recreating stale Phase 2 / GP approval language or overstating weak
walk-forward evidence.

Reviewed file:

```text
diagnostics/walk_forward_baseline.py
```

Current review result:

```text
The script currently includes a Current Status Override.
It states that walk-forward evidence is development only.
It states GP and Phase 2 are paused.
It no longer directly grants Phase 2 approval.
```

Remaining concern:

```text
The report can still say "YES. Simple baseline factors pass walk-forward
validation." when the aggregate pass count crosses a loose threshold.
In the current report, only 10 of 40 tests pass and no combo appears in the
"Consistent Performers (pass >= 3 of 5 windows)" table. This should not be
described as a clean walk-forward pass.
```

New instruction:

- Do not treat aggregate pass count alone as a walk-forward PASS.
- A baseline should be called `walk-forward pass` only if a specific
  factor/universe/TopN combo passes at least 3 of 5 windows and is named in the
  consistent performers table.
- If no combo meets that bar, the conclusion must be `partial / unstable
  evidence`, even if the total number of individual passing tests is above a
  loose threshold.
- Keep the `Current Status Override` in all generated walk-forward reports.
- Keep stating that Phase 2 and GP remain paused until final holdout reaches
  PASS under the runbook criteria.

Required future change:

- Update the report template so it never grants Phase 2 approval while final
  holdout is only `preliminary pass`.
- Update the pass/fail summary so it does not say simple baselines broadly pass
  when no stable combo passes at least 3 of 5 windows.
- If the script generates report copies, ensure `report/` and `analysis/` do not
  drift.
- Add or run a lightweight scan for stale unguarded phrases in `report/`,
  `analysis/`, `diagnostics/`, and `codexmd/`.

Suggested acceptance checks:

```powershell
python -m compileall diagnostics
python diagnostics\final_holdout_monitor_check.py
rg -n "Phase 2 .*can|proceed to Phase 2|restart GP|GP .*can" report analysis diagnostics codexmd
```

Any remaining stale phrase must either be removed from generated current reports
or clearly enclosed by a `Current Status Override` that says:

```text
Final holdout: preliminary pass
GP: paused
Phase 2: paused
```

The scan can match instructional examples inside `codexmd/`; those are
acceptable if they are clearly framed as blocked or stale wording.

---

## Near-Term Plan

1. Fix `diagnostics/walk_forward_baseline.py` report wording.
2. Regenerate affected walk-forward reports only after the generator is fixed.
3. Re-run final holdout monitor to confirm the governing status did not change.
4. Keep final holdout parameter set frozen:
   - Universe: `U3_volclose_mid60`
   - Factor: `-volume`
   - Portfolio: `long_only_top50`
   - Cost model: `turnover * cost_rate`
   - Holdout: `2026-01-01+`
5. Treat all generated performance numbers as preliminary until the holdout
   reaches the final PASS criteria.

---

## Data Update Plan

Current config has:

```text
DATA_END = 20260512
```

Before extending conclusions, audit the data update path separately:

- Verify qfq price usage.
- Verify weekly dates are real trading dates.
- Verify `signal_date` to `return_end_date` alignment.
- Verify source data files are not overwritten unexpectedly.
- Regenerate final holdout outputs only through:

```powershell
python diagnostics\final_holdout_audit.py
python diagnostics\final_holdout_monitor_check.py
```

---

## Final PASS Criteria

Do not promote beyond `preliminary pass` until all of the following are true:

1. At least 26 weekly holdout observations.
2. IR vs EW remains positive.
3. Cumulative excess return remains positive.
4. Weekly excess win rate remains above 50%.
5. Reports are regenerated from the single holdout script, not manually edited.
6. Walk-forward regime risks are cited alongside the final holdout result.
7. No stale report-generation source can recreate Phase 2 / GP approval wording.

Final PASS still does not mean production readiness. It only means the signal
has survived a more meaningful out-of-sample window and Phase 2 can be
considered under strict baseline comparison.

---

## Phase 2 Gate

If final PASS is eventually reached, Phase 2 should still begin conservatively:

- Keep `-volume` and `-ret_4w` as simple baselines.
- Any GP or new factor must beat the simple baseline under the same data,
  universe, cost, and reporting rules.
- Report long-only, long-short, and excess vs benchmark separately.
- Preserve train/validation/test/holdout boundaries.
- Record factor direction explicitly.

Until then:

```text
GP remains paused.
Phase 2 remains paused.
```

---

## Completion Definition For The Next Task

The next agent should finish with:

- Files changed.
- Why the change was made.
- Validation commands run.
- Whether any report was regenerated.
- Whether any backtest conclusion changed.
- Whether GP and Phase 2 remain paused.
- Remaining unsafe or preliminary conclusions.

---

## 2026-05-16 Review: `diagnostics/walk_forward_baseline.py`

Review scope:

```text
diagnostics/walk_forward_baseline.py
```

Impact assessment:

```text
Module: diagnostics / report governance
Data contract impact: no source data changes
Backtest metric impact: no metric formula change required by this review
Report impact: yes, generated walk-forward report wording and output copies
Experiment rerun needed: only regenerate the walk-forward diagnostic report
```

Current script status:

- The script now builds a `consistent` list for factor/universe/TopN combos
  that pass at least 3 of 5 walk-forward windows.
- The conclusion no longer treats aggregate pass count alone as a clean
  walk-forward PASS.
- If no consistent combo exists, the report says the evidence is partial and
  unstable, and explicitly blocks Phase 2 / GP.
- The `Current Status Override` remains present and says final holdout is
  `preliminary pass`, GP paused, Phase 2 paused.

Remaining instructions:

1. Regenerate the current walk-forward report from the updated script so stale
   generated files no longer say broad "YES" if no stable combo exists.
2. Update the script to write both report copies from the same generated text:

```text
report/walk_forward_baseline_report.md
analysis/walk_forward_baseline_report.md
```

3. Keep the result parquet in `report/` unless a separate tracked summary source
   is intentionally added.
4. Update the generated-files table in the report to list both markdown outputs.
5. Run:

```powershell
python diagnostics\walk_forward_baseline.py
python -m compileall diagnostics
python diagnostics\final_holdout_monitor_check.py
```

6. Scan for stale unguarded wording after regeneration:

```powershell
rg -n "YES\\. Simple baseline factors pass walk-forward|Phase 2 .*can|proceed to Phase 2|restart GP|final PASS" report analysis diagnostics codexmd
```

Matches inside `codexmd/` may be acceptable if they are clearly framed as
blocked, stale, or instructional examples. Current generated reports should not
contain unguarded approval language.

Required final state:

```text
Final holdout: preliminary pass
GP: paused
Phase 2: paused
Walk-forward evidence: development only
No broad PASS unless a named combo passes >= 3/5 windows
```

---

## 2026-05-16 Follow-up Review: `diagnostics/walk_forward_baseline.py`

Review scope:

```text
diagnostics/walk_forward_baseline.py
```

Current finding after full project scan:

```text
The earlier ANALYSIS_DIR issue is already fixed in the current codebase.
diagnostics/walk_forward_baseline.py now defines ANALYSIS_DIR, creates both
report/ and analysis/, and lists both markdown outputs in the report.
```

Current code status:

```text
REPORT_DIR = "report"
ANALYSIS_DIR = "analysis"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)
```

Remaining instruction:

- Keep the walk-forward script as a governed diagnostic, not a model-search
  launcher.
- Keep both markdown outputs synchronized.
- Do not use walk-forward as Phase 2 approval while final holdout is only
  `preliminary pass`.

Recommended verification:

```powershell
python diagnostics\walk_forward_baseline.py
python -m compileall diagnostics
python diagnostics\final_holdout_monitor_check.py
Compare-Object (Get-Content report\walk_forward_baseline_report.md) (Get-Content analysis\walk_forward_baseline_report.md)
```

Required final status after this fix:

```text
Final holdout: preliminary pass
GP: paused
Phase 2: paused
No new GP run
No Phase 2 start
No source data changes
```

---

## 2026-05-16 Full Project Scan And Quant Orders

The project was scanned across:

```text
config/
data/
diagnostics/
evaluation/
evolution/
factors/
pipeline/
portfolio/
report/
analysis/
codexmd/
docs/
```

Validation performed during scan:

```powershell
python -m compileall diagnostics factors evolution portfolio evaluation data pipeline config utils
python diagnostics\final_holdout_monitor_check.py
```

Observed data state:

```text
data/daily_ohlcv.parquet: 4,272,733 rows, 2023-01-03 to 2026-05-12
data/weekly_ohlcv.parquet: 871,552 rows, 2023-01-05 to 2026-05-08
data/weekly_daily_features.parquet: 871,552 rows, 17 columns, 2023-01-05 to 2026-05-08
report/walk_forward_baseline.parquet: 40 rows x 23 columns
final_holdout_monitor_check.py: OK
```

Current research facts:

- `walk_forward_baseline.py` is now a valid governed diagnostic.
- Walk-forward evidence is not stable: no factor/universe/TopN combo passes at
  least 3 of 5 windows.
- Final holdout remains `preliminary pass`, with 13 weekly observations.
- Existing GP infrastructure can generate expression-tree factors, but prior GP
  did not prove incremental value over simple baselines.
- Factor generation is currently constrained to daily-derived feature fields,
  which is good for avoiding raw level alpha, but it also means the next model
  work should first map and test the available feature set.

New quant direction:

```text
Stop issuing only report-format tasks.
Start building a controlled quant-model runway.
Do not start broad GP / Phase 2 yet.
```

### Order 1: Build Model Research Readiness Script

Create:

```text
diagnostics/model_research_readiness.py
```

Responsibilities:

1. Read `data/weekly_daily_features.parquet`.
2. Report available columns and missingness by period.
3. Recompute the frozen baseline pack:

```text
U3_volclose_mid60
-volume
-ret_4w
long_only_top50
long_only_top100
universe equal-weight benchmark
cost_rate = 0.004
```

4. Separate periods explicitly:

```text
train: 2023-01-01 to 2024-06-30
validation: 2024-07-01 to 2025-06-30
development/test: 2025-07-01 to 2025-12-31
final_holdout: 2026-01-01+
```

5. Output:

```text
report/model_research_readiness.json
report/model_research_readiness.md
analysis/model_research_readiness.md
```

6. State clearly:

```text
This prepares model comparison.
It does not approve Phase 2.
It does not restart GP.
It does not tune on final_holdout.
```

### Order 2: Build Candidate Factor Matrix Diagnostic

After readiness exists, create:

```text
diagnostics/candidate_factor_matrix.py
```

Allowed candidate families:

```text
weekly reversal: -ret_1w, -ret_4w, -ret_12w
weekly volatility: -vol_4w, -vol_12w
weekly activity: -volume, -amount, volume_z, amount_z
daily-derived: d_ret_5d, d_ret_20d, d_vol_20d, d_downside_vol_20d,
               d_range_20d, d_intraday_strength_5d,
               d_volume_z20, d_amount_z20
```

Rules:

- Evaluate candidates on train/validation/development windows only.
- Final holdout can be reported for the frozen baseline only, not used for
  selecting new factors.
- Every candidate must be compared to universe equal-weight and to the frozen
  simple baseline.
- Save machine-readable results:

```text
report/candidate_factor_matrix.parquet
report/candidate_factor_matrix_summary.json
report/candidate_factor_matrix.md
analysis/candidate_factor_matrix.md
```

### Order 3: Model Gate Before Any GP Restart

Before any broad GP or Phase 2 model search, require:

```text
1. model_research_readiness.py has run cleanly.
2. candidate_factor_matrix.py has identified at least one candidate that beats
   the frozen baseline on development windows without using final_holdout.
3. The candidate improvement is measured by excess return, IR vs EW, excess win
   rate, turnover, annualized cost, and relative drawdown.
4. The result is reproducible from a single script and written to report/ and
   analysis/.
5. A human explicitly approves a small model scout.
```

### Order 4: First Allowed Model Scout

Only after Orders 1-3 are complete, the first model run should be small and
bounded:

```text
diagnostics/light_model_scout.py
```

Allowed model types:

```text
ranked linear score
ridge/logistic-style rank model if sklearn is available
small decision tree only if fully documented
```

Forbidden in the first scout:

```text
broad GP
large random search
neural networks
final_holdout tuning
manual selection based on 2026 results
```

The first scout must output whether the model beats:

```text
-volume U3 LO50
-ret_4w U3 LO50
universe equal-weight
```

### Order 5: Current Go / No-Go

```text
Go now:
- model_research_readiness.py
- candidate_factor_matrix.py
- feature availability and missingness audit
- baseline comparison gate

No-go now:
- broad GP restart
- Phase 2 declaration
- final PASS declaration
- final_holdout-based model selection
```

This is the quant direction: build the controlled model runway first, then run a
small model scout only when the baseline and candidate matrix justify it.

---

## 2026-05-16 Post Orders 1-2 Review

The user reported Orders 1-2 are handled. The current commit includes:

```text
diagnostics/model_research_readiness.py
diagnostics/candidate_factor_matrix.py
report/model_research_readiness.md
analysis/model_research_readiness.md
report/candidate_factor_matrix.md
analysis/candidate_factor_matrix.md
```

Validation rerun:

```powershell
python diagnostics\model_research_readiness.py
python diagnostics\candidate_factor_matrix.py
python -m compileall diagnostics
python diagnostics\final_holdout_monitor_check.py
```

Result:

```text
Scripts run.
compileall passes.
final_holdout_monitor_check.py passes.
GP remains paused.
Phase 2 remains paused.
```

Important review findings:

1. Final holdout benchmark inconsistency has reappeared in the new readiness
   and candidate-matrix outputs.

```text
report/final_holdout_metrics.json:
  annualized_ew_return = +8.710%
  annualized_excess_return = +3.350%

report/model_research_readiness.json and report/candidate_factor_matrix.parquet:
  final_holdout univ_ew_annual_return = -31.620%
  final_holdout -volume LO50 excess = +3.350%
```

This is internally inconsistent. The new scripts appear to compute EW benchmark
metrics on a different index from the portfolio/excess series. This resembles
the previous final-holdout benchmark bug.

2. The candidate matrix uses a frozen U3 universe built from 2023-01-01 to
   2025-12-31. That is acceptable as a frozen development universe, but results
   for train and validation are not pure walk-forward/out-of-sample evidence.
   Do not use those rows to approve a model scout without a separate
   walk-forward universe check.

3. Candidate summaries currently treat raw activity factors such as `-amount`
   as strong candidates. These may be liquidity/attention/size-like exposures,
   not clean alpha. They need an exposure audit before promotion.

4. Baseline factors also appear in the candidate universe. Future summaries
   should distinguish:

```text
baseline factors: -volume, -ret_4w
new candidates: everything else
```

Do not say "candidate beats baseline" if the candidate set includes the
baseline factors without clear labeling.

### New Required Fix 1: Benchmark Alignment

Fix both scripts so all benchmark metrics use the same date index as the
portfolio/excess series.

In both scripts, change benchmark metric computation to align explicitly:

```python
ew = fwp.mean(axis=1)
ci = pf.index.intersection(ew.index)
strategy = pf["net_ret"][ci]
benchmark = ew[ci]
excess = strategy - benchmark
m_abs = portfolio_metrics(strategy)
m_ew = portfolio_metrics(benchmark)
m_exc = portfolio_metrics(excess)
```

Do this in:

```text
diagnostics/model_research_readiness.py
diagnostics/candidate_factor_matrix.py
```

Add a final-holdout consistency check for the frozen `-volume` U3 LO50 baseline:

```text
n_holdout_weeks == report/final_holdout_metrics.json["n_holdout_weeks"]
annualized_ew_return matches report/final_holdout_metrics.json["annualized_ew_return"]
annualized_excess_return matches report/final_holdout_metrics.json["annualized_excess_return"]
ir_vs_ew matches report/final_holdout_metrics.json["ir_vs_ew"]
```

Use a small tolerance for rounded values.

### New Required Fix 2: Universe Disclosure And Robustness

Rename/report the current universe as:

```text
frozen_development_universe: U3_volclose_mid60 built from 2023-01-01 to 2025-12-31
```

Add a warning:

```text
Train/validation rows under the frozen development universe are diagnostic only
and are not pure walk-forward evidence.
```

Before any model scout, add either:

```text
diagnostics/candidate_factor_matrix_walkforward.py
```

or an explicit walk-forward mode in `candidate_factor_matrix.py` that builds the
universe per window from data available before that validation window.

### New Required Fix 3: Candidate Promotion Gate

Do not proceed to `diagnostics/light_model_scout.py` yet.

First add a candidate-promotion summary that separates:

```text
baseline factors
raw activity candidates
daily-derived candidates
other weekly candidates
```

For each new candidate, require:

```text
beats baseline on dev_test by IR vs EW
positive excess annual return
weekly excess win rate > 50%
turnover not materially worse than baseline unless justified
no final_holdout used for selection
survives walk-forward universe check
```

Raw `-amount`, `-volume`, `volume_z`, and `amount_z` candidates require an
extra exposure note before promotion because they may be liquidity/attention
or size-like structural exposures.

### New Go / No-Go

```text
Go now:
- Fix benchmark alignment in readiness and candidate matrix scripts.
- Regenerate readiness and candidate matrix outputs.
- Add final-holdout consistency assertions against final_holdout_metrics.json.
- Add candidate-promotion summary that excludes baseline factors from
  "new candidate" claims.
- Add walk-forward universe robustness check for candidate factors.

No-go now:
- light_model_scout.py
- broad GP
- Phase 2 declaration
- final PASS declaration
- final_holdout-based candidate selection
```

Only after these fixes pass should the next agent propose the first bounded
`light_model_scout.py`.

---

## 2026-05-16 Resolution Of Claude Warnings

Claude's repeated warning was:

```text
13-week holdout is limited; raw activity candidates have exposure risk;
light_model_scout should wait until walk-forward universe check passes.
```

Current resolution:

1. The 13-week holdout limit is now a code-level gate.

```text
diagnostics/final_holdout_audit.py
diagnostics/final_holdout_monitor_check.py
```

The canonical metrics now include:

```text
final_pass_min_weeks = 26
final_pass_eligible = false
final_pass_blockers = ["holdout_weeks 13 < required 26"]
```

The monitor prints the blocker and will fail if a final PASS is claimed before
the minimum-week gate is satisfied.

2. Raw activity candidates now have an exposure audit.

```text
diagnostics/activity_exposure_audit.py
report/activity_exposure_audit.md
analysis/activity_exposure_audit.md
```

Result:

```text
raw_activity_gate = blocked_pending_neutralization_or_richer_exposure_audit
flagged factors = -volume, -amount, volume_z, amount_z
```

This does not invalidate the frozen `-volume` baseline. It blocks treating raw
activity candidates as newly promoted model features without neutralization or
richer exposure controls.

3. light_model_scout is now blocked by a walk-forward universe gate.

```text
diagnostics/candidate_factor_matrix_walkforward.py
report/candidate_factor_matrix_walkforward.md
analysis/candidate_factor_matrix_walkforward.md
```

Result:

```text
surviving_new_candidates = 0
model_scout_gate = blocked_no_candidate_survived_walk_forward
```

Although `-amount` performs well in several windows, it is raw activity and
therefore excluded from model promotion.

Validation run:

```powershell
python diagnostics\final_holdout_audit.py
python diagnostics\model_research_readiness.py
python diagnostics\candidate_factor_matrix.py
python diagnostics\activity_exposure_audit.py
python diagnostics\candidate_factor_matrix_walkforward.py
python diagnostics\candidate_factor_matrix.py
python -m compileall diagnostics factors evolution portfolio evaluation data pipeline config utils
python diagnostics\final_holdout_monitor_check.py
git diff --check
```

Current no-go state:

```text
Final holdout: preliminary pass
Final PASS: blocked until at least 26 holdout weeks
Raw activity promotion: blocked
light_model_scout: blocked
GP: paused
Phase 2: paused
```

Next instruction:

```text
Do not run light_model_scout yet.
Do not restart GP.
Do not enter Phase 2.
Do not promote raw activity candidates.

The next useful quant task is to design a non-raw candidate family that can
survive the same walk-forward universe gate, or add richer exposure data
such as market cap / industry / turnover neutralization before reconsidering
activity-like signals.
```
