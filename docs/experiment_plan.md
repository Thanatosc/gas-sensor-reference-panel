## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan
- Origin Date: 2026-08-14
- Verification Status: UNVERIFIED
- Version Label: code_plan_v1

## Experiment Overview

- **Title**: How Often Should an Electronic Nose Be Recalibrated?
- **Objective**: Estimate error recovery as a function of target-period reference
  budget under time-ordered sensor drift.
- **Hypothesis**: Drift can produce a practically material frozen-model error
  increase, while at least one light recalibration strategy recovers a meaningful
  fraction of the loss with 5% target references. The hypothesis is allowed to
  fail; the null result becomes a cost-saving decision boundary.
- **Type**: Secondary-data machine-learning benchmark and statistical analysis.

## Setup

- **Language/Framework**: Python 3.11+, NumPy, pandas, scikit-learn, optional
  XGBoost.
- **UCI 270 command**: `.\.venv\Scripts\python.exe scripts/run_benchmark.py --config configs/kill_test.json --input data/processed/uci270_normalized.csv --out-dir results/kill_test_v2`
- **UCI 360 command**: `.\.venv\Scripts\python.exe scripts/run_benchmark.py --config configs/kill_test_uci360.json --input data/processed/uci360_normalized.csv --out-dir results/kill_test_uci360_v1`
- **Working directory**: project root.
- **Environment**: CPU baseline; optional GPU is not required for the Kill Test.

## Inputs

| Input | Path | Description |
|---|---|---|
| UCI 270 normalized table | `data/processed/uci270_normalized.csv` | Batch-level concentration extension of UCI 224 |
| UCI 360 normalized table | `data/processed/uci360_normalized.csv` | CO/NOx/NO2 long table over three 90-day windows |
| configuration | `configs/experiment.json` | Frozen split, budgets, models, and endpoint parameters |

## Expected outputs

| Output | Path | Format | Success criterion |
|---|---|---|---|
| row-level benchmark | `results/tables/benchmark_results.csv` | CSV | non-empty; one row per valid combination |
| run manifest | `results/logs/run_manifest.json` | JSON | command, seed, config hash, package versions, and input hash present |
| audit report | `results/logs/dataset_audit.json` | JSON | status `PASS` before benchmark execution |

## Monitoring configuration

- **Timeout**: 30 minutes for the Kill Test; full matrix budget is advisory and
  may be split by dataset/model.
- **Monitor files**: `results/logs/run_manifest.json` and the result CSV.
- **Metric file**: `results/tables/benchmark_results.csv`.
- **Metric key**: `recovered_loss`.

## One-week Kill Test

Run UCI 270 batches 1-5 for PLS, Random Forest, and XGBoost at 0%, 5%, and 10%
reference budgets. Run the first three consecutive quarters of UCI 360 as the
independent confirmation panel. PASS requires either: (a) at least two corpora
show a frozen nRMSE relative increase of at least 20% and a light strategy
recovers at least 50% of the loss at 5%; or (b) all strategies recover less than
20% in both corpora with the same direction. Otherwise mark CONDITIONAL or FAIL
using the candidate document's definitions.

## Analysis guardrails

No post-hoc budget selection, no random row split across time, no independent
dataset count inflation, no cross-gas regression pooling, and no claim based on
a single gas or single sequence. A fixed 30% target holdout is never eligible as
reference data; budget samples are nested within the remaining 70%.
Evaluation is restricted to source/target common concentration support, and a
gas/batch sequence with fewer than two target concentration levels is skipped as
not regression-evaluable.
