# Figure package

Source: `results\confirmation_worner_v1\tables\benchmark_results.csv`  
Transformation script SHA-256: `8d8e4d354b50a290cbbcd34e5f77edb528d9bfeb842a23b4c29f0de0ce1a61a1`  
Rendering status: **PASS**

Figures use a colorblind-safe categorical palette, 300-dpi output, and separate analyte/model panels. Figure 3 uses absolute nRMSE change for the visual effect; the recovery ratio is retained in the tables with denominator diagnostics.

## Figure 1

**Caption.** Figure 1. Leakage-controlled temporal evaluation and reference-budget workflow. The first three batches are used for source fitting; each later target window is split into a labeled reference panel and a held-out test set before any recalibration is fitted. The primary absolute reference budgets are 0, 2, 5, 10, 20, and 50 observations.

**LaTeX.** `\includegraphics[width=\columnwidth]{figures/figure_01_workflow.pdf}`

**Trace claim.** The protocol preserves temporal order and selects reference observations before evaluating the held-out target set.

## Figure 2

**Caption.** Figure 2. Median held-out nRMSE across absolute reference budgets for each analyte and model. Lines show the frozen source model, lightweight output calibration, and full retraining; ribbons show the interquartile range across target windows. The nRMSE axis is logarithmic so that the complete two-reference instability remains visible without compressing the other budgets. Lower nRMSE is better. Models and analytes are displayed in separate panels and are not pooled as independent replicates.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_02_budget_curves.pdf}`

**Trace claim.** Performance changes with reference budget are heterogeneous across analytes and model classes.

## Figure 3

**Caption.** Figure 3. Target-window-specific change in nRMSE after lightweight calibration at the five-reference budget. Negative values indicate improvement relative to the frozen source model; positive values indicate worsening. Filled circles mark windows with recovery ≥0.50, filled triangles mark recovery <0.20, and open circles mark intermediate recovery. A black outline flags the descriptive small-denominator warning; no observations were excluded.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_03_primary_heterogeneity.pdf}`

**Trace claim.** At the primary budget, lightweight output calibration contains both useful and inadequate target-window/model regimes.

## Figure 4

**Caption.** Figure 4. Proportion of all evaluable target-window/model sequences jointly meeting the temporal-increase and recovery gates under the six-day primary analysis, the three-day-window sensitivity analysis, and the alternative reference-panel seed. Labels show numerator/denominator counts. The heterogeneous boundary is retained in both sensitivity analyses.

**LaTeX.** `\includegraphics[width=\columnwidth]{figures/figure_04_sensitivity.pdf}`

**Trace claim.** The presence of a heterogeneous lightweight boundary is stable to temporal-window width and reference-panel seed, while counts and regime medians vary.

