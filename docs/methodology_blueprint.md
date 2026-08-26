## Material Passport

- Origin Skill: academic-research-suite / deep-research + experiment-agent
- Origin Mode: plan
- Origin Date: 2026-08-14
- Verification Status: UNVERIFIED
- Version Label: methodology_blueprint_v1

## Research Question Brief

### Primary research question

Under a time-ordered evaluation protocol that preserves sensor drift and
environmental change, how much target-period reference concentration data is
required for each model and recalibration strategy to restore acceptable
concentration-estimation performance?

### Scope

In scope: concentration regression within gas identities; temporal batch and
location shifts; reference budgets of 0%, 1%, 2%, 5%, 10%, and 20%; PLS/linear,
Random Forest, XGBoost, and an optional small 1D model; UCI 270 as discovery,
UCI 251/322/360 and the 2025 one-year electronic-nose corpus as confirmation.

Out of scope: ordinary cross-batch gas classification as the primary task;
claiming batches are independent datasets; a new drift-compensation algorithm;
large deep networks; human-subject data collection.

## Methodology Blueprint

### Paradigm

Pragmatic quantitative benchmarking. The estimand is an operational decision
curve linking reference-sample cost to predictive-error recovery, so the design
prioritizes temporal validity and deployment relevance over algorithm novelty.

### Design and data strategy

1. Preserve the original timestamp, acquisition sequence, batch, location, and
   gas identity. Never random-shuffle rows across time before splitting.
2. Use early batches as source training data and later batches as target periods.
   The exact mapping is frozen in `configs/experiment.json` after the audit.
3. Sample target-period reference rows without replacement at each budget. The
   same seed and sampled row IDs are reused across strategies within a replicate.
   Before sampling, freeze 30% of each target gas/batch/location sequence as an
   evaluation holdout. All budgets draw nested samples from the remaining 70%,
   so target labels in the holdout are never used for fitting or selection.
   Build the nested reference order by alternating low and high concentration
   levels before moving inward, reflecting designed reference-gas calibration
   and preventing a small budget from containing only one concentration.
4. Treat each batch/location sequence as the inferential unit. Rows are only
   prediction units.
5. Use UCI 270, the concentration-bearing extension, for regression and keep
   UCI 224/270 in a single evidence family. Use later datasets and the
   Wörner et al. corpus as confirmation, not as extra replicates of the same
   source acquisition.
6. Restrict every gas/target-batch evaluation to concentration levels observed
   in both the source and target periods. Require at least two target
   concentration levels; otherwise record the sequence as not regression-
   evaluable instead of reporting nRMSE.

### Models and strategies

Models: PLS/linear baseline, Random Forest, XGBoost; a small 1D model is
optional and cannot block the core Kill Test.

Strategies: frozen model; full retraining with source plus references; prediction
calibrator update using target references; and target fine-tuning using only the
budgeted references. An oracle model trained with all target labels is used only
to define the loss-recovery denominator.

### Endpoints

Primary: `recovered_loss = (frozen_error - updated_error) /
(frozen_error - oracle_error)`. If the denominator is non-positive or not
finite, the row is marked undefined rather than clipped into a favorable value.

Secondary: MAE, RMSE/nRMSE, error by target concentration bin, and calibration
slope. Gas identity is a stratification/diagnostic variable, not the headline
classification endpoint.

### Statistical analysis

Fit and evaluate each gas identity separately. For each dataset, model,
strategy, budget, gas, and batch/location sequence,
report medians and paired bootstrap 95% CIs over sequences. Compare strategies
within the same sampled references. Apply Holm correction to the pre-specified
family of pairwise strategy contrasts. Do not count repeated rows as independent
observations.

The pre-drift reference error is the latest feasible rolling source validation:
train on source batches preceding the validation batch and score the latest
source batch with at least two shared concentration levels. Frozen target nRMSE
increase is measured relative to that reference.

### Validity and failure controls

- Temporal validity: an audit must verify monotonic order and non-overlapping
  source/target periods.
- Leakage control: target labels are visible only in sampled reference rows;
  target test rows are never used for fitting or selection.
- Construct validity: concentration is the target; gas identity is not used as a
  surrogate for accuracy.
- External validity: the Kill Test requires at least two evidence families or a
  conditional result with an explicit third-corpus follow-up.
- Reproducibility: record exact command, package versions, row IDs sampled, and
  configuration hash in the run manifest.

## Preregistration decision

Recommended: Yes. This is a secondary-data confirmatory benchmark with multiple
models, strategies, and budgets. Register the RQ, split, endpoints, and Kill Test
on OSF before inspecting final target-test results.

## Reporting standard

STROBE-style transparent reporting for observational/secondary data, with a
methods appendix containing the full benchmark matrix and data provenance.
