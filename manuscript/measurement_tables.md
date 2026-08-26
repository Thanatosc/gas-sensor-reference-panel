# Editable tables for the blind manuscript

## Table 1

**Five-reference performance summary.** Values are medians across four target
temporal windows. ΔnRMSE is the median of the window-level updated-minus-frozen
differences; it need not equal the difference between the two displayed medians.
Negative values indicate lower predictive error. IQRs and complete budget curves
are retained in the supplementary CSV. Models and windows are not treated as
independent replicates.

| Analyte | Model | Frozen nRMSE | Lightweight nRMSE | Lightweight ΔnRMSE | Lightweight recovery | Full-retrain nRMSE | Full-retrain ΔnRMSE | Full-retrain recovery |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Diacetyl | PLS | 0.307 | 0.248 | −0.063 | −0.340 | 0.232 | −0.072 | 0.548 |
| Diacetyl | Random forest | 0.132 | 0.070 | −0.045 | 0.467 | 0.060 | −0.062 | 0.741 |
| Diacetyl | XGBoost | 0.255 | 0.135 | −0.006 | −0.415 | 0.090 | −0.160 | 0.720 |
| Phenylethanol | PLS | 0.742 | 0.634 | −0.160 | 0.720 | 0.608 | −0.151 | 0.568 |
| Phenylethanol | Random forest | 0.490 | 0.683 | +0.193 | −1.861 | 0.495 | +0.005 | −0.120 |
| Phenylethanol | XGBoost | 0.503 | 0.576 | +0.072 | −0.493 | 0.539 | +0.019 | −0.159 |

## Table 2

**Smallest oracle denominators at the five-reference budget.** The 0.05 screen is
a descriptive warning only; no row is excluded or reweighted.

| Analyte | Target window | Model | Frozen nRMSE | Oracle nRMSE | Denominator | Lightweight ΔnRMSE | Recovery |
|---|---:|---|---:|---:|---:|---:|---:|
| Phenylethanol | 7 | XGBoost | 0.460 | 0.458 | 0.00181 | +0.570 | −315.025 |
| Diacetyl | 7 | Random forest | 0.004 | 0.002 | 0.00204 | −0.001 | 0.362 |
| Diacetyl | 7 | XGBoost | 0.004 | 0.001 | 0.00284 | +0.003 | −1.047 |
| Phenylethanol | 7 | Random forest | 0.441 | 0.424 | 0.01696 | +0.492 | −29.032 |
| Diacetyl | 7 | PLS | 0.156 | 0.128 | 0.02850 | +0.035 | −1.211 |

## Table 3

**Sensitivity of the primary decision boundary at five references.** Counts are
descriptive over analyte/model/temporal-window rows.

| Analysis | Lightweight rows | Drift-positive rows | Drift-conditioned recovery ≥0.50 | Drift-conditioned recovery <0.20 | Heterogeneous boundary | Full-retrain joint hits |
|---|---:|---:|---:|---:|---|---:|
| Six-day primary | 24 | 10 | 7 | 2 | Yes | 9 |
| Three-day windows | 42 | 21 | 12 | 6 | Yes | 19 |
| Alternative reference seed | 24 | 11 | 9 | 1 | Yes | 6 |
