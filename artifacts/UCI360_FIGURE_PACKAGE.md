# Figure package — UCI 360 recalibration analysis (CILS submission)

Source: `results\sensitivity_uci360_floor_grid\tables\benchmark_results.csv`  
Transformation script: `F:\CS\Paper\v3\c\scripts\generate_uci360_figures.py`  
Script SHA-256: `d43266332f6a1ae63cda4e95afdd8cf9587cb81b8aefd4d413436cf04658611d`  
Rendering status: **PASS**

Vector PDF at CILS column measures (single 3.35 in, double 6.9 in), serif face at 8 pt base, colourblind-safe palette, TrueType-embedded text. PNG copies at 600 dpi are for drafting only and should not be submitted.

All four figures replace the retired Wörner figure set in `results/figures/`, which describes the analysis withdrawn after the *Measurement* desk rejection.

## Per-budget values as plotted

| N | mean nRMSE | median nRMSE | mean ratio | median ratio | cells >2× | inverted slope | improved |
|---|---|---|---|---|---|---|---|
| 0 | 0.18414 | 0.13269 | 1.000 | 1.000 | 0 | 0 | 0/90 |
| 2 | 0.29585 | 0.14442 | 2.005 | 1.009 | 8 | 3 | 44/90 |
| 3 | 0.15913 | 0.14161 | 1.035 | 0.992 | 4 | 0 | 45/90 |
| 4 | 0.13608 | 0.13061 | 0.906 | 0.899 | 0 | 0 | 55/90 |
| 5 | 0.12930 | 0.12631 | 0.877 | 0.857 | 0 | 0 | 59/90 |
| 6 | 0.12218 | 0.12036 | 0.841 | 0.858 | 0 | 0 | 61/90 |
| 8 | 0.11446 | 0.11293 | 0.793 | 0.837 | 0 | 0 | 62/90 |
| 10 | 0.11223 | 0.10971 | 0.779 | 0.826 | 0 | 0 | 63/90 |
| 20 | 0.10857 | 0.10733 | 0.757 | 0.834 | 0 | 0 | 70/90 |
| 50 | 0.10563 | 0.10665 | 0.729 | 0.816 | 0 | 0 | 83/90 |

## Figures

### Figure 1 — Held-out error against reference budget, mean and median together

File: `figure_01_budget_curves.pdf` (double column)

**Caption.** Figure 1. Held-out nRMSE of lightweight output recalibration against the number of labelled target-window references $N$, pooled over 90 decision cells (3 analytes × 3 model classes × 10 target windows). (a) Absolute error, with the frozen source model shown for reference and the interquartile range of the recalibrated model shaded. (b) The same result as a ratio to the frozen model, with a double arrow marking the mean–median gap at $N=2$. Mean and median are plotted together because they disagree at the smallest budget: at $N=2$ the median cell is essentially unaffected (ratio 1.009) while the mean is inflated to 2.005 by a small number of cells. From $N=4$ both statistics fall below 1 together (0.906 mean, 0.899 median), and absolute error then falls monotonically in both mean and median across the remaining budgets. The mean–median divergence at $N=2$ is specific to draws in which the tail is realised: across the ten draws of Figure 5 the median at $N=2$ is 0.964–1.094, whereas the mean is 2.005 here and 0.979–1.149 in the other nine. Vertical axes are logarithmic in both panels; budgets are drawn at equal spacing, not to numeric scale, so that the small-panel region remains legible. Lower is better.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_01_budget_curves.pdf}`

**Claim.** The cost of a small reference panel appears in the mean but not the median, so it is a tail effect rather than a shift of the whole distribution.

**Limitations.** Cells share source-model fits and target windows and are not independent replicates, so the spread is descriptive rather than a confidence statement. The same reference panel supplies both the diagnostic and the calibrator fit, so panel size and diagnostic quality are not independent.

### Figure 2 — The heavy tail and its closure at four references

File: `figure_02_tail_decay.pdf` (double column)

**Caption.** Figure 2. (a) Ratio of recalibrated to frozen held-out nRMSE for every decision cell at each budget (90 cells per budget), coloured by analyte and jittered horizontally; open diamonds mark cells whose fitted calibration slope is negative. The bulk of the distribution lies near or below 1 at every budget, including $N=2$. (b) Number of cells exceeding twice the frozen error: 8 at $N=2$, 4 at $N=3$, and none from $N=4$ onward; the hatched overlay counts the subset with an inverted slope (3 cells, all at $N=2$). The three largest inflations are the three model classes of the same NO$_2$ window.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_02_tail_decay.pdf}`

**Claim.** In this panel draw the failures are isolated points rather than a shifted distribution, and the three most severe share one analyte-window and invert the calibration slope.

**Limitations.** This is one panel draw. The budget at which the count reaches zero is NOT reproducible across draws (Figure 5: 4, 6, 4, 20, 20) and must not be read as a floor. The tail is also concentrated rather than uniform, falling chiefly in one NO$_2$ window, so the count is neither a rate estimate nor a threshold.

### Figure 3 — Fitted calibration slope converging on unity

File: `figure_03_slope_convergence.pdf` (double column)

**Caption.** Figure 3. Distribution of the calibration slope against reference budget, where the plotted quantity is the slope of a regression of reference-analyser values on model predictions over the held-out test set and 1 is ideal. It is not the calibrator's own fitted coefficient. Boxes show the interquartile range and median with 5th–95th percentile whiskers; individual decision cells are overlaid. $N=0$ is the frozen model's held-out slope, that is, the distortion the calibrator is asked to remove (median 1.175). A two-point fit at $N=2$ can invert the slope entirely (minimum $-0.120$, 3 cells in the shaded inversion band), which reverses every prediction. No inversion occurs at any larger budget (minimum 0.354 at $N=3$). The median slope then approaches unity monotonically, from 0.786 at $N=2$ to 0.988 at $N=50$. Dispersion behaves differently and is printed above each box: the standard deviation is 0.240 at $N=2$, which is *smaller* than the 0.331 at $N=3$, because two-point fits are displaced downward as a group rather than scattered. Dispersion contracts decisively only at the largest budgets (0.126 at $N=20$ and 0.088 at $N=50$). Budgets are drawn at equal spacing, not to numeric scale.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_03_slope_convergence.pdf}`

**Claim.** Slope inversion on a two-point least-squares fit is the mechanism behind the tail, and it disappears as soon as a third reference is added; the median slope then approaches unity monotonically.

**Limitations.** The calibrator is fitted on the reference panel while this slope is evaluated on the held-out set, so the two are linked only through the panel draw. A single reference-panel seed is used. The standard deviation is not monotone in the budget, so it should not be read as a precision-improves-with-N statement on its own. A slope near 1 does not by itself imply small error, since it is insensitive to scatter about the calibration line.

### Figure 4 — Pre-decision diagnostic against realised benefit

File: `figure_04_diagnostic.pdf` (double column)

**Caption.** Figure 4. Reference-panel diagnostic $D_{\mathrm{ref}}$, computed before any recalibration decision, against the realised benefit $\Delta$nRMSE $=$ nRMSE$_{\mathrm{frozen}}-$nRMSE$_{\mathrm{lightweight}}$. Open circles are the rule-fitting windows 4–9, filled triangles the held-out windows 10–13. (a) At $N=5$ the diagnostic predicts the magnitude of the gain (Spearman $\rho=0.814$, $p=1.6\times 10^{-9}$ on held-out windows; $\rho=0.348$, $p=0.01$ on rule-fitting windows). (b) At $N=2$ the association is much weaker and no longer consistent across window sets ($\rho=0.372$, $p=0.025$ held-out; $\rho=-0.120$, $p=0.389$ rule-fitting; $\rho=0.201$, $p=0.057$ pooled). More important than the weakening is the direction of the failures: the three cells with the highest diagnostic values are the three catastrophic ones, so the association that survives at $N=2$ does not order cells by safety. Note the symmetric logarithmic vertical axis in (b), linear within $\pm0.1$, and the different vertical ranges of the two panels. A gate keyed on a high diagnostic therefore recommends recalibration exactly where a two-point fit is about to fail, which is why the prohibition has to be a hard constraint rather than something the diagnostic can manage.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_04_diagnostic.pdf}`

**Claim.** The diagnostic is informative about how much will be recovered above the exactly-determined panel, but it does not order cells by safety there. The reversal shown in (b) is specific to the one draw in five that realised an inversion; in the other four the top diagnostic quartile at $N=2$ is no worse than the rest.

**Limitations.** The diagnostic hypothesis was generated by inspecting an earlier three-window run of this corpus, so windows 4–9 are in-sample for hypothesis generation and windows 10–13 (121 previously untouched days) are the confirmation set. The same reference panel supplies both the diagnostic and the calibrator fit, so panel size and diagnostic quality are not independent. The rule-fitting association is reported for completeness and is not independent evidence.

### Figure 5 — The failure threshold does not replicate across panel draws

File: `figure_05_draw_sensitivity.pdf` (double column)

**Caption.** Figure 5. The same protocol under 10 independent reference-panel draws, each redrawing every panel and reseeding the model random states; the pre-specified draw is highlighted. (a) Worst nRMSE ratio observed in each draw, logarithmic scale. Inversion and inflation beyond fivefold occur at two references and at no other budget in any draw, and only the pre-specified draw realises them; above two references the worst outcome anywhere is 4.7-fold. (b) Number of cells above twice frozen error, with a tick marking each draw's first clean budget. Those budgets are 4, 6, 4, 20, 20, 4, 4, 5, 8, 4, so the apparently clean threshold of the pre-specified draw is a property of that panel realisation and not of the method. Every draw uses the same range-spanning design, so the spread is not a consequence of poor transfer-sample selection.

**LaTeX.** `\includegraphics[width=\textwidth]{figures/figure_05_draw_sensitivity.pdf}`

**Claim.** Unbounded failure is confined to the exactly-determined panel in every draw, while the reference count at which moderate failures cease varies by a factor of five across draws, with a mode at four.

**Limitations.** Five draws demonstrate instability but do not characterise its distribution; the per-draw first-clean budgets span 4 to 20 and the one-in-five rate at which inversion appeared is an observation, not an estimate. Draws share the corpus, the windows and the source fits, so they are replicates of the panel selection only.

