## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: validate
- Origin Date: 2026-08-15
- Verification Status: VERIFIED
- Version Label: confirmation_worner_v1

## Confirmation validation report

The frozen confirmation run contains 576 rows: two analytes, four target
windows, three models, four strategies, and six absolute reference budgets.
The primary decision budget is 5 labeled target-window observations.

### Decision-gate results

- Heterogeneous lightweight boundary (at least one recovery ≥0.50 and at least one <0.20 at the primary budget): **True**.
- Full-retraining joint hits (drift increase ≥0.20 and recovery ≥0.50 at the primary budget): **9**.
- These are descriptive counts over temporal windows; models are not treated as independent replicates.

| Analyte | Model | Sequences | Drift ≥20% | Light recovery ≥50% | Light recovery <20% | Drift-conditioned ≥50% | Drift-conditioned <20% | Median recovery | Range |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Diacetyl | pls | 4 | 3 | 2 | 2 | 2 | 1 | -0.340 | [-1.700, 1.007] |
| Diacetyl | random_forest | 4 | 2 | 2 | 1 | 2 | 0 | 0.467 | [-0.005, 0.791] |
| Diacetyl | xgboost | 4 | 2 | 1 | 2 | 1 | 1 | -0.415 | [-1.096, 0.611] |
| Phenylethanol | pls | 4 | 3 | 2 | 1 | 2 | 0 | 0.720 | [-1.976, 1.009] |
| Phenylethanol | random_forest | 4 | 0 | 0 | 3 | 0 | 0 | -1.861 | [-29.032, 0.282] |
| Phenylethanol | xgboost | 4 | 0 | 0 | 3 | 0 | 0 | -0.493 | [-315.025, 0.244] |

### Reproducibility

- Verdict: **REPRODUCIBLE_WITH_FLOATING_POINT_VARIATION**.
- Maximum absolute numeric difference: `3.694822225952521e-13`.
- Decision flags identical: `True`.
- CSV hashes can differ because multithreaded tree fitting changes the last floating-point bits; threshold decisions remain identical.

### Sensitivity analyses

| Analysis | Light rows | Drift ≥20% | Drift-conditioned ≥50% | Drift-conditioned <20% | Heterogeneous boundary | Full-retrain joint hits |
|---|---:|---:|---:|---:|---:|---:|
| Three-day windows | 42 | 21 | 12 | 6 | True | 19 |
| Alternative reference seed | 24 | 11 | 9 | 1 | True | 6 |

The heterogeneous boundary remains present under both pre-specified sensitivities, but regime medians move materially with the reference-panel seed. The paper must therefore report panel-design sensitivity rather than presenting one selected reference panel as definitive.
Common-support and observed-range analyses are structurally identical because each eligible window contains the same two levels per analyte. Missingness sensitivity is not applicable because the normalized concentration panel has no missing or non-finite features.

### Boundary conditions

- The 624-row pre-extracted feature table was not used as the primary panel because it omits three dates and is not the complete 700-file archive.
- The archive provides controlled temporal sequences but cannot isolate physical sensor drift from all environmental, maintenance, and concentration effects.
- The result does not justify a universal lightweight-recalibration claim; it evaluates when a lightweight output update is insufficient under this protocol.
