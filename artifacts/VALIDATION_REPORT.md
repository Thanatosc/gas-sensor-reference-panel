## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: 2026-08-14
- Verification Status: VERIFIED
- Version Label: validation_v1

## Validation Report

- **Source**: UCI 270 Kill Test v2 + UCI 360 Kill Test v1
- **Overall Confidence**: RED_FLAG for causal drift attribution; CAUTION for the numerical benchmark
- **Pre-specified Kill Test verdict**: **FAIL**
- **Rationale**: The two evidence families do not provide the pre-specified same-direction joint effect.

### Statistical Findings

Models are treatments, not independent replicates. Counts below are gas/batch
sequences within each model. Bootstrap intervals are medians over sequences;
with only 6 UCI 270 and 3 UCI 360 sequences per model, they are descriptive and
expected to be wide.

| Corpus | Model | Sequences | Drift >=20% | Light recovery >=50% | Joint hits | Light median recovery [95% bootstrap CI] | Full-retrain joint hits |
|---|---:|---:|---:|---:|---:|---:|---:|
| UCI 270 | pls | 6 | 3 | 0 | 0 | -0.666 [-23.673, 0.275] | 2 |
| UCI 270 | random_forest | 6 | 2 | 1 | 0 | -0.739 [-2.916, 0.247] | 1 |
| UCI 270 | xgboost | 6 | 2 | 3 | 0 | 0.167 [-382.424, 1.604] | 1 |
| UCI 360 | pls | 3 | 2 | 3 | 2 | 1.215 [1.109, 2.162] | 0 |
| UCI 360 | random_forest | 3 | 3 | 1 | 1 | 0.374 [0.016, 0.913] | 0 |
| UCI 360 | xgboost | 3 | 3 | 1 | 1 | 0.181 [0.025, 0.869] | 1 |

The lightweight strategy is `calibrator_update`. `full_retrain` is shown for
diagnosis but cannot satisfy the lightweight PASS condition. Recovery above 1
is possible when recalibration outperforms the full-reference oracle model;
negative values mean recalibration worsened nRMSE relative to the frozen model.

### Warnings

| Type | Detail | Affected |
|---|---|---|
| Data support | UCI 270 has no exact timestamps and 4/10 gas/batch combinations have only one common concentration; gas 6 is absent from target batches 4-5. | UCI 270 generalizability |
| Dataset shift | UCI 360 windows span seasonal and environmental change, so error change is not identifiable as sensor drift alone. | Causal drift claim |
| Oracle denominator | Recovery is undefined when the full-reference oracle does not improve on frozen. | One UCI 270 model/sequence |
| Multiple paths | v0-v2 method changes occurred after preliminary outputs and before preregistration. | Confirmatory interpretation |
| Small sequence count | Bootstrap operates on 3 or 6 sequences per model. | CI precision |

### Fallacy Scan

- **Coverage**: 11/11 fallacy types checked

| Fallacy | Severity | Detail |
|---|---|---|
| Simpson's paradox | CAUTION | Aggregate recovery reverses across analytes/models; only stratified results are defensible. |
| Ecological fallacy | NOTE | Inference is limited to dataset-level deployment sequences, not individual sensors or all electronic noses. |
| Berkson's paradox | CAUTION | UCI 360 uses complete cases; analyzer/sensor availability may select non-random hours. |
| Collider bias | CAUTION | Common-support and complete-case filtering may condition on variables affected by environment and instrument state. |
| Base-rate neglect | NOTE | Not a diagnostic classification analysis; base-rate metrics are not used. |
| Regression to the mean | NOTE | Periods were selected temporally, not for extreme error, but oracle-normalized recovery can amplify small denominators. |
| Survivorship bias | CAUTION | Missing analyzer hours are excluded; missingness patterns require a sensitivity analysis. |
| Look-elsewhere effect | CAUTION | Three models, multiple strategies, budgets, and targets were inspected; no inferential multiplicity claim is made yet. |
| Garden of forking paths | RED_FLAG | Method revisions followed v0/v1 diagnostics. Treat v2/v1 as exploratory until frozen and reproduced on untouched data. |
| Correlation != causation | RED_FLAG | Secondary observational sequences cannot isolate physical sensor drift from season, environment, maintenance, or concentration shift. |
| Reverse causality | NOTE | No directional causal relation between concentration and error recovery is claimed. |

### Reproducibility

- **Method**: exact command re-run in the same environment
- **Verdict**: REPRODUCIBLE

Execution reproducibility does not upgrade the causal interpretation. The Kill
Test verdict applies to the pre-specified two-corpus rule, not to whether a
revised full-retraining or replacement-boundary paper could still be viable.
