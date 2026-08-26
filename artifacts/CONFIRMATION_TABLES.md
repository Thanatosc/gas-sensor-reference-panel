# Confirmation tables for the Measurement manuscript

These tables are generated from the frozen Wörner confirmation CSV. The temporal target window is the aggregation unit; model rows are shown separately and are not treated as independent replicates. `delta_nrmse` is updated nRMSE minus frozen nRMSE, so negative values indicate improvement.

## Primary five-reference regime summary

| Analyte | Model | Strategy | n windows | nRMSE median [Q1, Q3] | ΔnRMSE median [Q1, Q3] | Recovery median [Q1, Q3] | denominator median [min, max] | |recovery| > 5 (n) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Diacetyl | pls | frozen | 4 | 0.307 [0.186, 0.425] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.133 [0.028, 0.301] | 0 |
| Diacetyl | pls | calibrator_update | 4 | 0.248 [0.203, 0.290] | -0.063 [-0.173, 0.050] | -0.340 [-1.334, 0.650] | 0.133 [0.028, 0.301] | 0 |
| Diacetyl | pls | full_retrain | 4 | 0.232 [0.178, 0.278] | -0.072 [-0.140, -0.012] | 0.548 [0.412, 0.590] | 0.133 [0.028, 0.301] | 0 |
| Diacetyl | random_forest | frozen | 4 | 0.132 [0.070, 0.177] | 0.000 [0.000, 0.000] | 0.000 [-0.000, 0.000] | 0.123 [0.002, 0.171] | 0 |
| Diacetyl | random_forest | calibrator_update | 4 | 0.070 [0.043, 0.085] | -0.045 [-0.101, -0.000] | 0.467 [0.270, 0.627] | 0.123 [0.002, 0.171] | 0 |
| Diacetyl | random_forest | full_retrain | 4 | 0.060 [0.040, 0.069] | -0.062 [-0.114, -0.014] | 0.741 [0.553, 0.859] | 0.123 [0.002, 0.171] | 0 |
| Diacetyl | xgboost | frozen | 4 | 0.255 [0.056, 0.463] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.251 [0.003, 0.544] | 0 |
| Diacetyl | xgboost | calibrator_update | 4 | 0.135 [0.046, 0.386] | -0.006 [-0.094, 0.121] | -0.415 [-1.059, 0.315] | 0.251 [0.003, 0.544] | 0 |
| Diacetyl | xgboost | full_retrain | 4 | 0.090 [0.044, 0.124] | -0.160 [-0.334, -0.012] | 0.720 [0.585, 0.747] | 0.251 [0.003, 0.544] | 0 |
| Phenylethanol | pls | frozen | 4 | 0.742 [0.619, 0.854] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.240 [0.119, 0.346] | 0 |
| Phenylethanol | pls | calibrator_update | 4 | 0.634 [0.509, 0.756] | -0.160 [-0.200, -0.060] | 0.720 [-0.146, 0.985] | 0.240 [0.119, 0.346] | 0 |
| Phenylethanol | pls | full_retrain | 4 | 0.608 [0.524, 0.669] | -0.151 [-0.185, -0.112] | 0.568 [0.554, 0.681] | 0.240 [0.119, 0.346] | 0 |
| Phenylethanol | random_forest | frozen | 4 | 0.490 [0.469, 0.516] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.083 [0.017, 0.165] | 0 |
| Phenylethanol | random_forest | calibrator_update | 4 | 0.683 [0.520, 0.866] | 0.193 [0.004, 0.397] | -1.861 [-9.767, -0.212] | 0.083 [0.017, 0.165] | 1 |
| Phenylethanol | random_forest | full_retrain | 4 | 0.495 [0.468, 0.519] | 0.005 [-0.014, 0.015] | -0.120 [-0.443, 0.100] | 0.083 [0.017, 0.165] | 0 |
| Phenylethanol | xgboost | frozen | 4 | 0.503 [0.491, 0.518] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.112 [0.002, 0.178] | 0 |
| Phenylethanol | xgboost | calibrator_update | 4 | 0.576 [0.514, 0.736] | 0.072 [-0.005, 0.245] | -0.493 [-79.405, -0.031] | 0.112 [0.002, 0.178] | 1 |
| Phenylethanol | xgboost | full_retrain | 4 | 0.539 [0.523, 0.559] | 0.019 [0.014, 0.041] | -0.159 [-13.101, -0.133] | 0.112 [0.002, 0.178] | 1 |

## Decision matrix for the lightweight update

The pre-specified descriptive gates are frozen nRMSE relative increase ≥ 0.20, recovery ≥ 0.50, and inadequate recovery < 0.20. The denominator screen (<0.05 nRMSE units) is a warning only; it does not remove observations or alter any gate.

| Analyte | Target window | Model | Frozen nRMSE | Updated nRMSE | ΔnRMSE | Oracle denominator | Recovery | Drift ≥20% | Recovery ≥50% | Recovery <20% | Small denominator warning |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---|---|
| Diacetyl | 4 | pls | 0.449 | 0.289 | -0.160 | 0.301 | 0.532 | True | True | False | False |
| Diacetyl | 5 | pls | 0.417 | 0.208 | -0.210 | 0.208 | 1.007 | True | True | False | False |
| Diacetyl | 6 | pls | 0.196 | 0.292 | 0.096 | 0.057 | -1.700 | True | False | True | False |
| Diacetyl | 7 | pls | 0.156 | 0.191 | 0.035 | 0.028 | -1.211 | False | False | True | True |
| Diacetyl | 4 | random_forest | 0.192 | 0.056 | -0.135 | 0.171 | 0.791 | True | True | False | False |
| Diacetyl | 5 | random_forest | 0.172 | 0.083 | -0.090 | 0.157 | 0.572 | True | True | False | False |
| Diacetyl | 6 | random_forest | 0.092 | 0.093 | 0.000 | 0.089 | -0.005 | False | False | True | False |
| Diacetyl | 7 | random_forest | 0.004 | 0.003 | -0.001 | 0.002 | 0.362 | False | False | False | True |
| Diacetyl | 4 | xgboost | 0.544 | 0.212 | -0.332 | 0.544 | 0.611 | True | True | False | False |
| Diacetyl | 5 | xgboost | 0.436 | 0.910 | 0.474 | 0.433 | -1.096 | True | False | True | False |
| Diacetyl | 6 | xgboost | 0.073 | 0.059 | -0.015 | 0.069 | 0.216 | False | False | False | False |
| Diacetyl | 7 | xgboost | 0.004 | 0.007 | 0.003 | 0.003 | -1.047 | False | False | True | True |
| Phenylethanol | 4 | pls | 0.835 | 0.515 | -0.320 | 0.317 | 1.009 | True | True | False | False |
| Phenylethanol | 5 | pls | 0.912 | 0.752 | -0.160 | 0.346 | 0.464 | True | False | False | False |
| Phenylethanol | 6 | pls | 0.532 | 0.768 | 0.236 | 0.119 | -1.976 | False | False | True | False |
| Phenylethanol | 7 | pls | 0.649 | 0.489 | -0.159 | 0.163 | 0.976 | True | True | False | False |
| Phenylethanol | 4 | random_forest | 0.501 | 0.522 | 0.021 | 0.056 | -0.376 | False | False | True | False |
| Phenylethanol | 5 | random_forest | 0.562 | 0.516 | -0.047 | 0.165 | 0.282 | False | False | False | False |
| Phenylethanol | 6 | random_forest | 0.478 | 0.844 | 0.366 | 0.109 | -3.345 | False | False | True | False |
| Phenylethanol | 7 | random_forest | 0.441 | 0.933 | 0.492 | 0.017 | -29.032 | False | False | True | True |
| Phenylethanol | 4 | xgboost | 0.505 | 0.513 | 0.008 | 0.067 | -0.123 | False | False | True | False |
| Phenylethanol | 5 | xgboost | 0.559 | 0.515 | -0.044 | 0.178 | 0.244 | False | False | False | False |
| Phenylethanol | 6 | xgboost | 0.501 | 0.637 | 0.136 | 0.158 | -0.864 | False | False | True | False |
| Phenylethanol | 7 | xgboost | 0.460 | 1.030 | 0.570 | 0.002 | -315.025 | False | False | True | True |

## Sensitivity summary

| Analysis | Light rows | Drift ≥20% | Drift-conditioned recovery ≥50% | Drift-conditioned recovery <20% | Heterogeneous boundary | Full-retrain joint hits |
|---|---:|---:|---:|---:|---|---:|
| six_day_primary | 24 | 10 | 7 | 2 | True | 9 |
| three_day_windows | 42 | 21 | 12 | 6 | True | 19 |
| alternative_reference_seed | 24 | 11 | 9 | 1 | True | 6 |

## Interpretation guard

The recovered-loss ratio is retained because it was part of the frozen protocol, but it can become numerically unstable when the frozen-to-oracle nRMSE denominator is small. The manuscript should therefore lead with absolute nRMSE and ΔnRMSE, report the denominator diagnostics, and avoid interpreting extreme ratios as standalone evidence. Temporal changes are descriptive and are not identified as physical sensor drift.
