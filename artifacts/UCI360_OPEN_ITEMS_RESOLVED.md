# UCI 360 — Resolution of Open Items 1–3

- Date: 2026-08-26
- Script: `scripts/analyze_open_items.py`
- Outputs: `results/open_items_uci360/{strategy_comparison,window_descriptives,panel_conditioning}.csv`
- Inputs: `results/sensitivity_uci360_floor_grid/tables/benchmark_results.csv`,
  `data/processed/uci360_rewindowed.csv`, `configs/sensitivity_uci360_floor_grid.json`
- Status: **VERIFIED** against the frozen benchmark; frozen models refitted with
  the same seed and split routine, so the reproduced `frozen_nrmse` and `ratio`
  match the benchmark table.

These close items 1, 2, and 3 of `UCI360_PRIMARY_FINDINGS.md`. Item 4 (venue) and
item 5 (disclosures) were closed separately: CILS was selected, and both
disclosures are carried in the figure package caption fields.

---

## Item 1 — `target_finetune` at small budgets

Mean held-out nRMSE over the same 90 decision cells per budget:

| N | frozen | lightweight | target-only refit | full retraining |
|---|---|---|---|---|
| 0 | 0.18414 | 0.18414 | 0.18414 | 0.18414 |
| **2** | 0.18414 | **0.29585** | **0.45609** | 0.17326 |
| 3 | 0.18414 | 0.15913 | 0.20231 | 0.17215 |
| 4 | 0.18414 | **0.13608** | 0.17755 | 0.16756 |
| 5 | 0.18414 | 0.12930 | 0.15960 | 0.16599 |
| 6 | 0.18414 | 0.12218 | 0.14546 | 0.15999 |
| 8 | 0.18414 | 0.11446 | 0.13161 | 0.15635 |
| 10 | 0.18414 | 0.11223 | 0.12450 | 0.15325 |
| 20 | 0.18414 | 0.10857 | 0.11431 | 0.14006 |
| 50 | 0.18414 | 0.10563 | **0.10265** | 0.12257 |

Cells above twice frozen error:

| N | lightweight | target-only refit | full retraining |
|---|---|---|---|
| 2 | 8 | **35** | 0 |
| 3 | 4 | 25 | 0 |
| 4 | **0** | 12 | 0 |
| 5 | 0 | 7 | 0 |
| 6 | 0 | 5 | 0 |
| 8 | 0 | **0** | 0 |

`target_finetune` discards the source model and fits only on the target
references. At N = 2 its mean nRMSE is 0.456, worst ratio 40.5×, and **35 of 90
cells** exceed twice the frozen error against 8 for lightweight calibration. Its
tail does not close until **N = 8**, twice the lightweight floor, and it only
overtakes lightweight calibration at N = 50 (0.1027 against 0.1056).

Its two summaries disagree, the same trap the paper's headline rests on: mean
nRMSE drops below frozen at **N = 4** (0.17755 vs 0.18414), but the mean per-cell
ratio does not fall below 1 until **N = 8** (0.9260), which is also where its tail
closes. Verified structurally: source 3600 × 22, budget set
[0,2,3,4,5,6,8,10,20,50], frozen mean constant at 0.184138.

Full retraining never exceeds twice frozen error at any budget, because the
source data dominates the fit; its mean improves slowly and monotonically
(0.1733 at N = 2 to 0.1226 at N = 50) and it is the worst of the three update
strategies from N = 5 onward.

**One-sentence version for the manuscript.** Retaining the source model and
correcting only its output is what makes a small panel usable at all: discarding
the source model needs eight labelled references to become tail-safe and fifty to
become competitive, while full retraining is tail-safe at every budget but never
recovers as much.

This ordering also states the scope of the floor claim: **N = 4 is the floor for
output recalibration specifically**, not a universal minimum reference count.

---

## Item 3 — What is distinctive about NO₂ window 6

### The window

| gas | window | rows | distinct targets | min | max | range | mean | skew |
|---|---|---|---|---|---|---|---|---|
| NO₂ | 4 | 652 | 169 | 16 | 233 | 217 | 103.6 | 0.34 |
| NO₂ | 5 | 655 | 160 | 5 | 206 | 201 | 98.7 | 0.25 |
| **NO₂** | **6** | **362** | **106** | 5 | **171** | **166** | **66.0** | **0.60** |
| NO₂ | 7 | 428 | 166 | 2 | 225 | 223 | 108.5 | 0.16 |
| NO₂ | 8 | 479 | 132 | 29 | 194 | 165 | 89.5 | 0.56 |
| NO₂ | 9 | 658 | 208 | 13 | 288 | 275 | 126.0 | 0.34 |
| NO₂ | 10 | 478 | 158 | 27 | 269 | 242 | 123.0 | 0.34 |
| NO₂ | 11 | 672 | 200 | 17 | 333 | 316 | 137.9 | 0.27 |
| NO₂ | 12 | 615 | 210 | 25 | 310 | 285 | 154.2 | 0.10 |
| NO₂ | 13 | 710 | 191 | 29 | 248 | 219 | 132.3 | 0.23 |

Window 6 has the **fewest rows** (362 against 428–710), the **fewest distinct
reference values** (106 against 132–210), the **lowest mean concentration**
(66.0 against 89.5–154.2), and the **strongest right skew** (0.60). Its range is
not the narrowest — window 8 spans 165 against window 6's 166 — so the
distinguishing features are sparsity and low concentration, not range alone.
Values are the raw window distributions, before the common-support restriction
and before the held-out split.

### The mechanism, stated exactly

The reference panel is ordered to span the target range, so the first two
references drawn are one row from the lowest quantile stratum and one from the
highest. In window 6 those rows carry **27.0 and 118.0 µg/m³** (not the window
extremes of 5 and 171, which mostly fall in the held-out split). All three frozen
models place them in the wrong order:

| model | panel targets | frozen predictions | true gap | predicted gap | calibrator coefficient | held-out ratio |
|---|---|---|---|---|---|---|
| PLS | 27.0, 118.0 | 116.60, 112.33 | +91.0 | **−4.27** | **−21.32** | 44.5× |
| random forest | 27.0, 118.0 | 117.32, 107.66 | +91.0 | **−9.66** | **−9.42** | 23.8× |
| XGBoost | 27.0, 118.0 | 122.64, 110.94 | +91.0 | **−11.70** | **−7.78** | 19.8× |

For a two-point panel the least-squares calibrator coefficient is exactly the
ratio of the true gap to the predicted gap. The frozen models compress a 91
µg/m³ interval into a 4–12 µg/m³ interval **of the wrong sign**, so the
coefficient is large and negative and every prediction is inverted. The
compression, not the sign alone, sets the magnitude: a coefficient of −21 arises
because the denominator is small as well as negative.

Note the two distinct slope quantities. The calibrator coefficient above is the
multiplier applied to the frozen output. The `calibration_slope` column in the
benchmark table, plotted in Figure 3, is a different diagnostic: the slope of
reference values regressed on predictions over the **held-out** set, where 1 is
ideal and the same three cells read −0.050, −0.102, −0.120.

### Why N = 2 is uniquely dangerous: no residual degrees of freedom

| N | residual d.f. | median panel residual RMSE | min panel rank agreement | cells > 2× |
|---|---|---|---|---|
| **2** | **0** | **0.0000** | **0.000** | 8 |
| 3 | 1 | 4.547 | 0.333 | 4 |
| 4 | 2 | 11.346 | 0.500 | **0** |
| 5 | 3 | 14.202 | 0.500 | 0 |
| 6 | 4 | 15.886 | 0.600 | 0 |
| 8 | 6 | 18.014 | 0.679 | 0 |

A two-parameter calibrator fitted on two points reproduces both exactly. The
panel residual is identically zero, so **no panel-internal evidence of failure
can exist at N = 2**. The calibrator is unfalsifiable from the data that produced
it. From N = 3 the panel can contradict the fitted line, and the residual becomes
informative.

### A partial guard, reported as a lead rather than a rule

**Provenance: this diagnostic is post-hoc.** It was constructed after the N = 2
failures were observed. It is not part of the frozen protocol and is not among
H1–H3.

The sign of the predicted gap over the two references separates the inversion
subclass perfectly: the 3 cells with a non-positive predicted gap are exactly the
3 largest inflations (44.5×, 23.8×, 19.8×), and no other cell has a non-positive
gap. This is checkable before any decision, from the panel alone.

It does not close the floor, for two reasons:

1. The remaining **5 of 8** cells above 2× at N = 2 have *positive* predicted
   gaps (median ratio 0.56, range up to 0.71). Their failure is slope error under
   compression, not inversion, and the sign test does not see it.
2. At N = 3 the four surviving failures look **clean** on the panel: rank
   agreement 1.000 and Pearson r 0.981–0.999 in every case, with calibrator
   coefficients 1.48–1.94. Only the panel residual is mildly elevated (median
   13.4 against 4.05 for the rest), which is far too weak to gate on.

| N=3 cell | panel targets | rank agreement | panel r | calibrator coefficient | ratio |
|---|---|---|---|---|---|
| CO w13 XGBoost | 0.5, 0.7, 4.9 | 1.000 | 0.9990 | 1.767 | 2.05 |
| NOx w4 random forest | 30, 40, 261 | 1.000 | 0.9916 | 1.557 | 2.17 |
| NOx w4 XGBoost | 30, 40, 261 | 1.000 | 0.9925 | 1.480 | 2.04 |
| NOx w5 PLS | 14, 47, 275 | 1.000 | 0.9808 | 1.936 | 2.10 |

Every one of these panels has two closely spaced low references and one distant
high reference, so the fit is determined by a single leveraged point and looks
perfect on its own data.

**Conclusion, and it strengthens rather than weakens the main claim.** A search
for a cheaper panel-side guard was made and it does not hold. Inversion is
detectable; the compression and leverage failures that remain at N = 2 and N = 3
are not. The operational answer therefore has to be the **hard floor at N = 4**,
not a diagnostic, and the reason is structural: below the floor the calibrator
either cannot be checked at all (N = 2) or is checked against a panel geometry
that hides the failure (N = 3).

---

## Item 2 — Tables

Regenerated against this corpus in `manuscript/uci360_tables.md`, replacing
`manuscript/measurement_tables.md`, which describes the retired Wörner analysis.
The retired file is left untouched.

---

## Carried forward

- The `d_ref` diagnostic remains the pre-specified one and is unaffected: it
  predicts *how much* is recovered above the floor and, as Figure 4 shows, is
  highest exactly where the two-point fit fails.
- Both required disclosures are unchanged: hypothesis provenance (windows 4–9
  in-sample for hypothesis generation) and the shared-panel confound.
- Nothing above revises a verdict, a threshold, or a window boundary.
